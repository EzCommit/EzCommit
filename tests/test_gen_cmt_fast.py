import pytest
from unittest.mock import AsyncMock, MagicMock
from ..controller.controller import Controller
from ..model.model import Model
from ..view.view import View

@pytest.fixture
def mock_model(mocker):
    mocker.patch('model.model._execute', new=AsyncMock(return_value=("mock_output", "")))
    mocker.patch('model.model._get_openai_answer', new=AsyncMock(return_value="mock_commit_message"))
    return Model(context_path=None, convention_path=None)

@pytest.fixture
def mock_view(mocker):
    return mocker.create_autospec(View, instance=True)

@pytest.fixture
def controller(mock_model, mock_view):
    ctrl = Controller({'context_path': None, 'convention_path': None})
    ctrl.model = mock_model
    ctrl.view = mock_view
    return ctrl

def test_generate_commit_no_changes(controller, mock_model):
    mock_model.get_changes_no_split = MagicMock(return_value="")
    mock_model.get_files_content = MagicMock(return_value=[])
    
    response = controller.model.generate_commit(stages=False, temperature=0.8)
    assert response == "No changes found"

def test_generate_commit_with_changes(controller, mock_model):
    mock_model.get_changes_no_split = MagicMock(return_value="mock_diff_output")
    mock_model.get_files_content = MagicMock(return_value=[("file1.py", "print('Hello, World!')")])
    
    response = controller.model.generate_commit(stages=False, temperature=0.8)
    assert response == "mock_commit_message"

def test_generate_commit_increase_temperature(controller, mock_model):
    mock_model.get_changes_no_split = MagicMock(return_value="mock_diff_output")
    mock_model.get_files_content = MagicMock(return_value=[("file1.py", "print('Hello, World!')")])
    
    controller.model.generate_commit = MagicMock(side_effect=["commit_message_1", "commit_message_2"])
    user_input = "r"

    controller.view.display_generated_commit = MagicMock(side_effect=[user_input, "a"])
    
    controller.generate_commit()
    
    assert controller.model.generate_commit.call_count == 2

def test_generate_commit_commit_message(controller, mock_model):
    mock_model.get_changes_no_split = MagicMock(return_value="mock_diff_output")
    mock_model.get_files_content = MagicMock(return_value=[("file1.py", "print('Hello, World!')")])
    
    controller.model.generate_commit = MagicMock(return_value="commit_message")
    controller.model.commit = AsyncMock()

    controller.view.display_generated_commit = MagicMock(return_value="c")
    
    controller.generate_commit()

    controller.model.commit.assert_called_once_with("commit_message")

def test_generate_commit_abort(controller, mock_model):
    mock_model.get_changes_no_split = MagicMock(return_value="mock_diff_output")
    mock_model.get_files_content = MagicMock(return_value=[("file1.py", "print('Hello, World!')")])
    
    controller.model.generate_commit = MagicMock(return_value="commit_message")
    controller.model.commit = AsyncMock()

    controller.view.display_generated_commit = MagicMock(return_value="a")
    
    controller.generate_commit()

    controller.model.commit.assert_not_called()