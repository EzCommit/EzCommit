from git import Repo
from enum import Enum
from typing import List

class Key(Enum):
    USER_EMAIL = 'user.email'
    USER_NAME = 'user.name'
    REMOTE_URL = 'remote.origin.url'
    REMOTE_FETCH_URL = 'remote.origin.fetch' 


class Repository:
    def __init__(self, config):
        self.config = config
        self.repo = Repo(config.repo_path)
        self.repo_path = config.repo_path

    def get_repo_name(self):
        try:
            origin_url = self.repo.remotes.origin.url
            
            if origin_url.endswith('.git'):
                origin_url = origin_url[:-4]
            
            parts = origin_url.split('/')
            if origin_url.startswith('git@github.com:'):
                full_name = origin_url.split(':')[1]
            elif origin_url.startswith('https://github.com/'):
                full_name = '/'.join(origin_url.split('/')[-2:])
            else:
                print("URL is not from GitHub")
                return None

            return full_name
        except Exception as e:
            print(f"Error fetching repository name: {e}")
            return None
    
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
