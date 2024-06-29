import chromadb
import git
import subprocess
from openai import OpenAI
from .utils import split_text_into_line_chunks
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from ..rag.ingest import Ingest

from ..constants import (
    COMMIT_COLLECTION
)


class RAG():
    def __init__(self, config):
        self.config = config
        self.repo = git.Repo(self.config.repo_path)
        self.client = chromadb.PersistentClient(path=config.db_path)
        self.collection = self.client.get_or_create_collection(name=COMMIT_COLLECTION)
        self.llm_client = OpenAI(api_key=self.config.openai_api_key)

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
            response = self.llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
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
    
    def _create_commit_message(self, similar_diffs, diff, convention, temperature):
        prompt = "New change:\n" + diff + "\n\n"
        prompt += "Previous similar changes:\n"
        for i, similar_diff in enumerate(similar_diffs):
            prompt += f"Similar change {i+1}:\n{similar_diff}\n\n"
        prompt += "\n\nCreate a one-line commit message according to one of the following convention formats:\n" + convention

        response = self.llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=temperature
        )

        return response.choices[0].message.content.strip()
        