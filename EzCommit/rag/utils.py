import difflib
import subprocess

def split_text_into_line_chunks(text, chunk_size=4096):
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
    parent_commit = commit.parents[0] if commit.parents else None
    if parent_commit:
        diff_cmd = ['git', 'diff', parent_commit.hexsha, commit.hexsha]
        diff_output = subprocess.check_output(diff_cmd, cwd=repo_path)
        diff_text = diff_output.decode('utf-8')
        
        summaries = []
        for chunk in split_text_into_line_chunks(diff_text):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": f"Summarize the following git diff:\n{chunk}\nSummary:"}
                ],
                max_tokens=500
            )
            summary = response.choices[0].message.content
            summaries.append(summary)
        
        return "\n".join(summaries)
    else:
        return "Initial commit - no parent diff available."