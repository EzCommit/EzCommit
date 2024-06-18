import git
import chromadb

from .utils import get_commit_diff
from constants import (
    REPO_PATH,
    COMMIT_COLLECTION
)

def update_database():
    repo = git.Repo(REPO_PATH)
    client = chromadb.PersistentClient(path="db")
    collection = client.get_or_create_collection(COMMIT_COLLECTION)
    for commit in repo.iter_commits():
        existing_commit = collection.get(ids=[commit.hexsha])
        if existing_commit['ids']:
            print(f"Skipping commit {commit.hexsha} as it already exists in the database.")
            continue

        commit_diff = get_commit_diff(commit, REPO_PATH)
        print(f"Processing commit {commit.hexsha}")

        collection.add(
            ids=[commit.hexsha],
            documents=[commit_diff],
            metadatas=[{"author": commit.author.name, "date": commit.committed_datetime.isoformat()}]
        )