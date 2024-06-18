import chromadb
from openai import OpenAI
from .utils import split_text_into_line_chunks
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from .ingest import update_database
import subprocess


from constants import (
    COMMIT_COLLECTION,
    REPO_PATH
)

OPENAI_API_KEY = 'sk-proj-vM0b19a4YCxOHYcuPoEwT3BlbkFJGQASmoQHIIb2FZ1KTdRW'

class RAG():
    def __init__(self):
        update_database()
        self.client = chromadb.PersistentClient(path='db')
        self.collection = self.client.get_collection(name=COMMIT_COLLECTION)
        self.llm_client = OpenAI(api_key=OPENAI_API_KEY)
        self.embedding_function = DefaultEmbeddingFunction()

    def generate_commit_message(self):
        # Xây dựng lệnh git diff
        diff_cmd = ['git', 'diff']
        
        # Thực hiện lệnh và lấy kết quả
        result = subprocess.check_output(diff_cmd, cwd=REPO_PATH)
        diff = result.decode('utf-8')
        
        # Tạo embedding cho git diff mới
        summaries, embedding = self._embed_diff(diff)

        similar_diffs = self._query_similar_diffs(embedding)
        commit_message = self._create_commit_message(similar_diffs, summaries)
        
        print(commit_message)


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
    
    def _create_commit_message(self, similar_diffs, diff):
        prompt = "Dựa trên các thay đổi sau và các thay đổi tương tự trước đây, hãy tạo một commit message: \n\n"
        prompt += "Thay đổi mới:\n" + diff + "\n\n"
        prompt += "Các thay đổi tương tự trước đây:\n"
        for i, similar_diff in enumerate(similar_diffs):
            prompt += f"Thay đổi tương tự {i+1}:\n{similar_diff}\n\n"

        response = self.llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        
        # Trích xuất commit message từ kết quả của ChatGPT
        commit_message = response.choices[0].message.content.strip()
        
        return commit_message