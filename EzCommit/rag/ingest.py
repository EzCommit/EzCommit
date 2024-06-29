from .utils import get_commit_diff
from ..constants import (
    COMMIT_COLLECTION
)

class Ingest:
    def __init__(self, client, llm_client, repo, config):
        self.client = client 
        self.llm_client = llm_client
        self.repo = repo
        self.config = config
    
    def update_database(self):
        collection = self.client.get_or_create_collection(COMMIT_COLLECTION)
        for commit in self.repo.iter_commits():
            existing_commit = collection.get(ids=[commit.hexsha])
            if existing_commit['ids']:
                continue

            commit_diff = get_commit_diff(commit, self.config.repo_path, self.llm_client)
            print(f"Processing commit {commit.hexsha}")

            collection.add(
                ids=[commit.hexsha],
                documents=[commit_diff],
                metadatas=[{"author": commit.author.name, "date": commit.committed_datetime.isoformat()}]
            )