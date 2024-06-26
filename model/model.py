from rag.rag import RAG
import requests
import subprocess
import asyncio
from typing import List, Optional
import subprocess
from github import Github, Auth


from constants import (
    OPENAI_API_KEY,
    CONTEXT_PATH_DEFAULT
)
from pathlib import Path
from openai import AsyncOpenAI

from model.repository import Repository
from rag.utils import split_text_into_line_chunks

async def _commit(repo_path:str, msg: str) -> list:
    cwd = repo_path
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

    
def _get_openai_answer(client, prompt: str, temperature: float) -> str:
    response = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        model="gpt-3.5-turbo-0125",
        temperature=temperature,
        top_p=1,
        max_tokens=500,
    )

    return response.choices[0].message.content




    
class Model:
    def __init__(self, config):
        self.config = config
        self.rag = RAG(self.config)
        self.repository = Repository(self.config)

        # self.context_path = Path(config.context_path) if config.context_path else None
        self.convention_path = Path(config.convention_path) if config.convention_path else None

        if self.convention_path:
            try: 
                self.convention = "Given this is the context of the commit message: \n"
                self.convention += self.convention_path.read_text() + "\n"
            except (FileNotFoundError, IOError) as e:
                print(f"Error reading context file: {e}")
                self.context = "Context file could not be read.\n"
        else: 
            self.convention = ''

    def create_pr_content(self, branch_a, branch_b):
        # self.repository.repo.git.checkout(branch_a)
        # self.repository.repo.remotes.origin.pull()
        # self.repository.repo.git.checkout(branch_b)
        # self.repository.repo.remotes.origin.pull()

        summaries = []
        for commit in self.repository.repo.iter_commits(f'{branch_b}..{branch_a}'):
            parent_commit = commit.parents[0] if commit.parents else None
            if parent_commit:
                stdout, stderr = asyncio.run(_execute(self.repository.repo_path, 'diff', [parent_commit.hexsha, commit.hexsha]))
                for chunk in split_text_into_line_chunks(stdout):
                    response = self.rag.llm_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": f"Summarize the following git diff:\n{chunk}\nSummary:"}
                        ],
                        max_tokens=500
                    )
                    summaries.append(response.choices[0].message.content)


        prompt_content = """
            Based on the following summarized commit messages, create a professional pull request description that consolidates all changes into a single PR. The description should be well-structured and presented in Markdown format. It should include the following sections:
            * Title: A concise title for the pull request.
            * Description: A brief overview of what this pull request does.
            * Changes: A detailed list of changes introduced by the commits.
            * Testing: Instructions on how to test the changes.
            * Related Issues: References to any related issues or tickets.
            * Checklist: A checklist to ensure that all steps have been completed before merging.\n
        """
        prompt_content += "\n".join(summaries)
        content = _get_openai_answer(self.rag.llm_client, prompt_content, 0.8)

        prompt_title = "Based on the following summarized commit messages, create a professional pull request title that consolidates all changes into a single PR."
        prompt_title += "\n".join(summaries)
        title = _get_openai_answer(self.rag.llm_client, prompt_title, 0.8)

        return content, title

    def create_pull_request(self, repo_name, branch_a, branch_b, content, title):
        auth = Auth.Token("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")
        g = Github(auth=auth)
        print(repo_name)
        repo = g.get_repo(repo_name)
        pr = repo.create_pull(
            title=title,
            body=content,
            head=branch_a,
            base=branch_b
        )
            


    def get_current_branch(self):
        return self.repository.repo.active_branch.name

    def list_all_branches(self):
        try:
            branches = [head.name for head in self.repository.repo.heads]
            return branches
        except Exception as e:
            print(f"Có lỗi xảy ra: {e}")
            exit(1)
        


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

    def commit(self, msg: str):
        asyncio.run(_commit(self.config.repo_path, msg))

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
