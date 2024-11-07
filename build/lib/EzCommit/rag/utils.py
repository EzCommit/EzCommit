import difflib
import subprocess
from mistralai.models import SDKError
import time
def split_text_into_line_chunks(text, chunk_size=2048):
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_length = 0

    for line in lines:
        line_length = len(line) + 1  # +1 for the newline character
        if current_length + line_length > chunk_size:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(line)
        current_length += line_length

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks



def get_commit_diff(commit, repo_path, client):
    wait_time = 1
    parent_commit = commit.parents[0] if commit.parents else None
    if parent_commit:

        diff_cmd = ['git', 'diff', parent_commit.hexsha, commit.hexsha]
        diff_output = subprocess.check_output(diff_cmd, cwd=repo_path)
        diff_text = diff_output.decode('utf-8')
        summaries = []
        for chunk in split_text_into_line_chunks(diff_text):

            try:
                response = client.chat.complete(
                    model="open-mistral-7b",
                    messages=[
                        {"role": "user", "content": f"Summarize the following git diff:\n{chunk}\nSummary:"}
                    ],
                    max_tokens=500
                )
                summary = response.choices[0].message.content
                summaries.append(summary)
            except SDKError as e:
                if "Status 429" in str(e):
                    print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    wait_time *= 2  # exponential backoff
                else:
                    raise  # re-raise other exceptions if they're not 429 errors

        return "\n".join(summaries)
    else:
        return "Initial commit - no parent diff available."