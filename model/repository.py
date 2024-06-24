from git import Repo
from enum import Enum
from typing import List

from constants import (
    REPO_PATH,
    OPENAI_API_KEY
)

class Key(Enum):
    USER_EMAIL = 'user.email'
    USER_NAME = 'user.name'
    REMOTE_URL = 'remote.origin.url'
    REMOTE_FETCH_URL = 'remote.origin.fetch' 

class Repository:
    def __init__(self):
        self.repo = Repo(REPO_PATH)
        self.repo_path = REPO_PATH
    
    async def get_config(self, key: Key) -> str:
        try:
            return self.repo.git.config('--get', key.value)
        except GitCommandError as e:
            return f"Error: {e}"

    async def get_configs(self, keys: List[Key]) -> dict:
        return {key: await self.get_config(key) for key in keys}

    async def set_config(self, key: str, value: str) -> str:
        try:
            self.repo.git.config(key, value)
            return "Config set successfully"
        except GitCommandError as e:
            return f"Error: {e}"

    async def getObjectDetails(self, treeish: str, path: str):
        try:
            return self.repo.git.cat_file('-p', f"{treeish}:{path}")
        except GitCommandError as e:
            return f"Error: {e}"
