from rag.rag import RAG
import subprocess
import asyncio
from typing import List
from enum import Enum
from git import Repo

from constants import (
    REPO_PATH,
    OPENAI_API_KEY
)
from pathlib import Path
from openai import AsyncOpenAI

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

async def _diff_files(repository: Repository, options: list = []) -> list:
    cwd = repository.repo_path
    cmd = "diff"
    full_options = [
        "--name-only",
        *options,
        "HEAD",
    ]

    stdout, stderr = await _execute(cwd, cmd, full_options)

    if stderr:
        print(f"stderr for 'git {cmd}' command:", stderr)

    lines = stdout.split("\n")
    return [line for line in lines if line]

async def _diff_detail_no_split(repository: Repository, options: list = []) -> list:
    cwd = repository.repo_path
    cmd = "diff"
    full_options = []

    stdout, stderr = await _execute(cwd, cmd, full_options)

    if stderr:
        print(f"stderr for 'git {cmd}' command:", stderr)
    
    return stdout

async def _get_file_content(repository: Repository, file_path: str) -> str:
    try:
        with open(f"{repository.repo_path}/{file_path}", 'r') as file:
            return file.read()
    except Exception as e:
        return f"Error: {e}"
    
async def _commit(repository: Repository, msg: str) -> list:
    cwd = repository.repo_path
    cmd = "commit"
    full_options = ['-a', '-m', msg]
    stdout, stderr = await _execute(cwd, cmd, full_options)
    
async def _get_openai_answer(api_key: str, prompt: str, temperature: float) -> str:
    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        model="gpt-3.5-turbo-0125",
        temperature=temperature,
        top_p=1,
        max_tokens=100,
    )
    return response.choices[0].message.content

class Model:
    def __init__(self, context_path: str = None, convention_path: str = None):
        self.repository = Repository()
        self.rag = RAG()
        self.context_path = Path(context_path) if context_path else None
        self.convention_path = Path(convention_path) if convention_path else None
        self.context = ""
        self.convention = ""

        if self.context_path:
            assert self.context_path.exists(), "Context file does not exist"
            self.context = "Given this is the context of the commit message: \n"
            self.context += self.context_path.read_text() + "\n"
        if self.convention_path:
            assert self.convention_path.exists(), "Convention file does not exist"
            self.convention = "Given this is the convention of the commit message: \n"
            self.convention += self.convention_path.read_text() + "\n"
            print("Path:", self.convention_path)

    def create_commit(self):
        self.rag.generate_commit_message()

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

    def get_changes_no_split(self):
        staged_changes = asyncio.run(_diff_detail_no_split(self.repository))
        return staged_changes

    def get_modified_files(self):
        modified_files = asyncio.run(_diff_files(self.repository))
        if not modified_files:
            print("No modified files found")
        return modified_files
    
    def get_files_content(self):
        modified_files = self.get_modified_files()
        if not modified_files:
            return []

        file_contents = []
        for file in modified_files:
            content = asyncio.run(_get_file_content(self.repository, file))
            file_contents.append((file, content))
        
        return file_contents

    def generate_commit(self, temperature: float):
        all_changes = self.get_changes_no_split()
        files_content = self.get_files_content()
        if len(files_content) == 0:
            return "No changes found"

        prompt = self.context + self.convention
        for file, content in files_content:
            prompt += "This is the current code in " + file + """, the code end after  "CODE END HERE!!!\n\n"""
            prompt += content + "\n"
            prompt += "CODE END HERE!!!\n\n"

        prompt += """This is the output after using git diff command, the output end after "GIT DIFF END HERE!!!\n\n"""
        prompt += all_changes + "\n"
        prompt += "GIT DIFF END HERE!!!\n\n"

        prompt += "Write a simple commit message for the changes. Don't need to explain. Read the code carefully, don't miss any changes."

        response = asyncio.run(_get_openai_answer(api_key=OPENAI_API_KEY, prompt=prompt, temperature=temperature))
        return response

    def commit(self, msg: str):
        asyncio.run(_commit(self.repository, msg))

    def get_visual_log(self):
        try:
            log_output = self.repository.repo.git.log(
                            '--graph','--full-history','--all', '--color',   
                            '--pretty=format: %C(bold blue)%d %C(reset) %C(green) %cd %C(reset) %s %C(cyan)(%an)%C(reset)',
                            '--date=short')
        except GitCommandError as e: 
            print("No commits found")
            return
        return log_output
    
    def get_pr_changes(self, pr_num = 1):
        try:
            current_branch = self.repository.active_branch 
            merge_commits = self.repository.git.rev_list(
                "--merges", "--first-parent", current_branch.name
            ).splitlines()

            # Get the first (latest) merge commit directly
            commit_hash = merge_commits[pr_num - 1] 
            commit = self.repository.commit(commit_hash)
            parent_commit = commit.parents[0]

            pr_log = self.repository.git.log(
                        f"{parent_commit.hexsha}..{commit_hash}",
                        "--pretty=format:%s",  # Get only commit messages
                        "--no-merges"  # Exclude the merge commit itself
                    ).splitlines()


            pr_diff = self.repository.git.diff(parent_commit.hexsha, commit_hash)
            return [pr_log, pr_diff]
            
        except GitCommandError as e:
            return(f"Error: {e}")
        except IndexError as e:
            return("Error: No merge commits found on this branch.")


    def summarize_changes(self, pr_num, temperature: float):
        pr_log, pr_diff = self.get_pr_changes(pr_num)
        if len(pr_diff) == 0:
            return "No changes found"

        prompt += """This is the output after using git diff command, the output end after "GIT DIFF END HERE!!!\n\n"""
        prompt += pr_diff + "\n"
        prompt += "GIT DIFF END HERE!!!\n\n"
        prompt += """This is the output after using git log command, the output end after "GIT LOG END HERE!!!\n\n"""
        prompt += pr_log + "\n"
        prompt += "GIT LOG END HERE!!!\n\n"
        prompt += "Write a descriptive and informative summaries for the changes. Don't need to explain. Read the code carefully, don't miss any changes."

        response = asyncio.run(_get_openai_answer(api_key=OPENAI_API_KEY, prompt=prompt, temperature=temperature))
        return response
