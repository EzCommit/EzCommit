from rag.rag import RAG
import subprocess
import asyncio
from typing import List
import subprocess

from constants import (
    REPO_PATH,
    OPENAI_API_KEY,
    CONTEXT_PATH_DEFAULT
)
from pathlib import Path
from openai import AsyncOpenAI

from model.repository import Repository

async def _commit(msg: str) -> list:
    cwd = REPO_PATH
    cmd = "commit"
    full_options = ['-m', msg]
    stdout, stderr = await _execute(cwd, cmd, full_options)
    print(stderr)
    return stdout


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
    full_options = [
        *options,
    ]

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
    def __init__(self, context_path, convention_path):
        self.repository = Repository()
        self.rag = RAG()

        if context_path == None:
            context_path = CONTEXT_PATH_DEFAULT

        self.context_path = Path(context_path)
        self.convention_path = Path(convention_path) if convention_path else None
        self.context = ""
        self.convention = ""

        self.context = "Given this is the context of the commit message: \n"
        self.context += self.context_path.read_text() + "\n"

        if self.convention_path:
            assert self.convention_path.exists(), "Convention file does not exist"
            self.convention = "Given this is the convention of the commit message: \n"
            self.convention += self.convention_path.read_text() + "\n"

    def create_commit_message(self, all_changes: bool, temperature: float = 0.8):
        if all_changes:
            asyncio.run(_execute(self.repository.repo_path, "add", ["."]))

        all_changes_with_staged = asyncio.run(_diff_detail_no_split(self.repository, ['--cached']))
        commit_message = self.rag.generate_commit_message(all_changes_with_staged, self.convention, temperature)

        return commit_message

    def get_changes(self):
        staged_changes = asyncio.run(_diff_detail(self.repository, '--cached'))
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
    
    def generate_commit(self, stages: bool, temperature: float):
        if stages:
            asyncio.run(_execute(self.repository.repo_path, "add", ["."]))

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
        #response = "yes"
        return response

    def commit(self, msg: str):
        asyncio.run(_commit(msg))

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
