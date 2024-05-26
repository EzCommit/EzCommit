from git import Repo, GitCommandError
import subprocess
import asyncio
from typing import List
from enum import Enum

class Key(Enum):
    USER_EMAIL = 'user.email'
    USER_NAME = 'user.name'
    REMOTE_URL = 'remote.origin.url'
    REMOTE_FETCH_URL = 'remote.origin.fetch' 

class Repository:
    def __init__(self, repo_path: str):
        self.repo = Repo(repo_path)
        self.repo_path = repo_path
    
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



async def _execute(cwd: str, subcommand: str, options: List[str] = []) -> (str, str):
    command = ["git"] + [subcommand] + options
    try:
        result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return "", f"Command failed with exit code {e.returncode}: {e.stderr}"

async def _diff_detail(repository: Repository, options: list = []) -> list:
    cwd = repository.repo_path
    cmd = "diff"
    full_options = [
        "--color",
        *options,
    ]

    stdout, stderr = await _execute(cwd, cmd, full_options)

    if stderr:
        print(f"stderr for 'git {cmd}' command:", stderr)

    lines = stdout.split("\n")
    return [line for line in lines if line]

async def _diff_index(repository: Repository, options: list = []) -> list:
    cwd = repository.repo_path
    cmd = "diff-index"
    full_options = [
        "--name-status",
        "--find-renames",
        "--find-copies",
        "--no-color",
        *options,
        "HEAD",
    ]

    stdout, stderr = await _execute(cwd, cmd, full_options)

    if stderr:
        print(f"stderr for 'git {cmd}' command:", stderr)

    lines = stdout.split("\n")
    return [line for line in lines if line]



class GitModel:
    def __init__(self):
        self.repository = Repository('/Users/minhvu/Documents/cnpmai/CLItest/csv-diff')

    def get_changes(self):
        staged_changes = asyncio.run(_diff_detail(self.repository))
        if staged_changes:
            print("Found staged changes")
            return staged_changes
        print("Staging area is empty. Using unstaged files (tracked files only still).")
        all_changes = asyncio.run(_diff_index(self.repository))
        if not all_changes:
            print("No changes found")
        return all_changes

