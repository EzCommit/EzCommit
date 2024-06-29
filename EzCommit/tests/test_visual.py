import subprocess
import pytest
from ..controller.controller import Controller
from ..model.model import Model
from ..view.view import View

from git import GitCommandError

@pytest.fixture(scope="module")
def run_visual_command():
    """Fixture to run the main script with the --visual flag and capture output."""
    result = subprocess.run(["python", "main.py", "--visual"], capture_output=True, text=True)
    return result.stdout

def test_visual_output(run_visual_command):
    """Asserts key elements of the visual output."""

    assert run_visual_command, "Output is empty"

    assert "Commits History Visualization" in run_visual_command, "Title not found"
    assert "*" in run_visual_command, "Graph characters not found"

def test_empty_repository(tmpdir):
    """Asserts a GitCommandError when the repository is empty."""
    with tmpdir.as_cwd():
        subprocess.run(["git", "init"])
        with pytest.raises(GitCommandError, match="No commits found."):
            subprocess.run(["python", "main.py", "--visual"], capture_output=True, text=True)

def test_invalid_repository(tmpdir):
    """Asserts a GitCommandError for invalid repository paths."""
    with tmpdir.as_cwd():
        with pytest.raises(GitCommandError, match="fatal: not a git repository"):
            subprocess.run(["python", "main.py", "--visual"], capture_output=True, text=True)
