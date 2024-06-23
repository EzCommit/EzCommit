import subprocess
import pytest

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
    #assert "Author:" in run_visual_command, "Author information not found"
