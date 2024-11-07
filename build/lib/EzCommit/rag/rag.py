import chromadb
import git
import subprocess
from mistralai import Mistral
from .utils import split_text_into_line_chunks
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.embeddings import FakeEmbeddings
from uuid import uuid4

from EzCommit.rag.ingest import Ingest

from EzCommit.constants import (
    COMMIT_COLLECTION
)


class RAG():
    def __init__(self, config):
        self.config = config
        self.repo = git.Repo(self.config.repo_path)
        self.client = chromadb.PersistentClient(path=config.db_path)
        self.collection = self.client.get_or_create_collection(name=COMMIT_COLLECTION)
        #self.llm_client = OpenAI(api_key=self.config.openai_api_key)
        self.llm_client = Mistral(api_key=self.config.mistral_api_key)
        self.ingest = Ingest(self.client, self.llm_client, self.repo, self.config)
        self.ingest.update_database()
        self.embedding_function = DefaultEmbeddingFunction()

    def generate_commit_message(self, diff, convention, temperature):
        summaries, embedding = self._embed_diff(diff)
        similar_diffs = self._query_similar_diffs(embedding)
        commit_message = self._create_commit_message(similar_diffs, summaries, convention, temperature)
        
        return commit_message


    def _embed_diff(self, diff):
        summaries = []
        for chunk in split_text_into_line_chunks(diff):
            response = self.llm_client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {"role": "user", "content": f"Summarize the following git diff:\n{chunk}\nSummary:"}
                ],
                max_tokens=500
            )
            summary = response.choices[0].message.content.strip()
            summaries.append(summary)
        
        summaries = "\n".join(summaries)
        return summaries, self.embedding_function([summaries])[0]
    
    def _query_similar_diffs(self, embedding):
        results = self.collection.query(query_embeddings=[embedding], n_results=5)
        return results['documents']
    
    def _query_info_readme(self):
             # Load
        loader = GenericLoader.from_filesystem(
            self.config.repo_path,
            glob="**/*",
            suffixes=[".py", ".ipynb"],
            exclude=["**/non-utf8-encoding.py"],
            parser=LanguageParser(language=Language.PYTHON, parser_threshold=500),
        )
        documents = loader.load()
        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON, chunk_size=2000, chunk_overlap=200
        )
        texts = python_splitter.split_documents(documents)
        embeddings = FakeEmbeddings(size=4096)
        vector_store = Chroma(collection_name="codebase", embedding_function=embeddings)
        uuids = [str(uuid4()) for _ in range(len(texts))]
        vector_store.add_documents(documents = texts, ids = uuids)

        query = "Primary entry file initializing application setup, key configurations, API integrations, main logic handling application entry, core modules, dependencies and orchestrating critical workflows. "
        result = vector_store.search(query=query, search_type="mmr", k=len(texts)//3)
        docs = ""
        for i in range(len(result)):
            docs += "Document " + str(i+1) + ":\n" + result[i].page_content + "\n\n"
        return docs
    

    def _create_commit_message(self, similar_diffs, diff, convention, temperature):
        prompt = "New change:\n" + diff + "\n\n"
        prompt += "Previous similar changes:\n"
        for i, similar_diff in enumerate(similar_diffs):
            prompt += f"Similar change {i+1}:\n{similar_diff}\n\n"
        prompt += "\n\nCreate a one-line commit message according to one of the following convention formats:\n" + convention

        response = self.llm_client.chat.complete(
            model="open-mistral-7b",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150, 
            temperature=temperature
        )

        return response.choices[0].message.content.strip()
        