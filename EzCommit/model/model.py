from ..rag.rag import RAG
import tempfile
import os
import markdown
import pdfkit


import requests
import subprocess
import asyncio
from typing import List, Optional
import subprocess
from github import Github, Auth


from ..constants import (
    CONTEXT_PATH_DEFAULT
)
from pathlib import Path
from openai import AsyncOpenAI

from ..model.repository import Repository
from ..rag.utils import split_text_into_line_chunks
from ..helper import default

async def _commit(repo_path:str, msg: str) -> list:
    cwd = repo_path
    cmd = "commit"
    full_options = ['-m', msg]
    stdout, stderr = await _execute(cwd, cmd, full_options)
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
        auth = Auth.Token("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")
        self.g = Github(auth=auth)
        self.repo_github = self.g.get_repo(self.repository.get_repo_name())

        self.context_path = Path(config.context_path) if config.context_path else None
        self.convention_path = Path(config.convention_path) if config.convention_path else None

        if self.convention_path:
            try: 
                self.convention = "Given this is the convention of the commit message: \n"
                self.convention += self.convention_path.read_text() + "\n"
            except (FileNotFoundError, IOError) as e:
                print(f"Error reading context file: {e}")
                self.context = "Context file could not be read.\n"
        else: 
            self.convention = default

        if self.context_path:
            try:
                self.convention = "Given this is the context of the repository: \n"
                self.context = self.context_path.read_text()
            except (FileNotFoundError, IOError) as e:
                print(f"Error reading context file: {e}")
                self.context = "Context file could not be read.\n"
        else:
            self.context = ''

    def list_pr(self):
        pull_requests = self.repo_github.get_pulls(state='all')

        return pull_requests

    def summarize_pr(self, pr, temp):
        structure = """
            # Title
            ## Introduction
            ## Major Changes
            ### New Features
            ### Bug Fixes
            ### Performance Improvements
            ### UI Enhancements
            ### Security
            ## Conclusion
        """
        summarise = []
        for commit in pr.get_commits():
            parent_commit = commit.parents[0] if commit.parents else None
            if parent_commit:
                stdout, stderr = asyncio.run(_execute(self.repository.repo_path, 'diff', [parent_commit.sha, commit.sha]))
                for chunk in split_text_into_line_chunks(stdout):
                    response = self.rag.llm_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": f"Summarize the following git diff:\n{chunk}\nSummary:"}
                        ],
                        max_tokens=500,
                        temperature = temp
                    )
                    summarise.append(response.choices[0].message.content)

        prompt = "You are a professional AI assistant that helps publish summary reports on changes in source code. Below is the report request. Please summarize the changes and publish the report in Markdown format. No codeblock"
        prompt += f'\n{structure}\n'
        prompt += "\n".join(summarise)

        content = _get_openai_answer(self.rag.llm_client, prompt, 0.8)
        return content



    def create_pr_content(self, branch_a, branch_b, temp):
        try:
            print(f"Checking out and pull {branch_b}")
            self.repository.repo.remotes.origin.pull(refspec=f'{branch_b}:{branch_b}')
        except Exception as e:
            print(e)


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
                        max_tokens=500,
                        temperature = temp
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

        prompt_title = "Based on the following summarized commit messages, create a professional pull request title that consolidates all changes into a single PR. Output should be contain only title.\n"
        prompt_title += "\n".join(summaries)
        title = _get_openai_answer(self.rag.llm_client, prompt_title, 0.8)

        return content, title

    def create_pull_request(self, branch_a, branch_b, content, title):
        pr = self.repo_github.create_pull(
            title=title,
            body=content,
            head=branch_a,
            base=branch_b
        )

        return pr
            


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

        response = _get_openai_answer(self.rag.llm_client, prompt=prompt, temperature=temperature)
        #response = "yes"
        return response

    def commit(self, msg: str):
        asyncio.run(_commit(self.config.repo_path, msg))

    def get_visual_log(self):
        try:
            log_output = self.repository.repo.git.log(
                            '--graph','--full-history','--all', '--no-color',   
                            '--pretty=format: %C(bold blue)%d %C(reset) %C(green) %cd %C(reset) %s %C(cyan)(%an)%C(reset)',
                            '--date=short')
        except GitCommandError as e: 
            print("No commits found")
            return
        return log_output

    def md_to_pdf(self, md_content: str, filename: str):
        export_dir = os.path.expanduser('~/ezcommit_export')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        def get_unique_filename(filename: str) -> str:
            base = filename.strip()
            unique_filename = os.path.join(export_dir, f"{base}.pdf")
            counter = 1
            while os.path.exists(unique_filename):
                unique_filename = os.path.join(export_dir, f"{base} ({counter}).pdf")
                counter += 1
            return unique_filename

        with tempfile.TemporaryDirectory() as tempdir:
            markdown_path = os.path.join(tempdir, 'content.md')

            # Lưu nội dung markdown vào file
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            html_path = os.path.join(tempdir, 'content.html')

            html_content = markdown.markdown(md_content)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            pdf_path = os.path.join(tempdir, 'output.pdf')

            pdfkit.from_file(html_path, pdf_path)

            with open(pdf_path, 'rb') as f:
                pdf_output = f.read()

            output_pdf_path = get_unique_filename(filename)
            with open(output_pdf_path, 'wb') as f:
                f.write(pdf_output)
                f.close()