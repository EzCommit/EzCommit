import pytest
from unittest.mock import AsyncMock, MagicMock, call, patch
from ..controller.controller import Controller
from ..model.model import Model
from ..view.view import View

@pytest.fixture
def mock_model(mocker):
    mocker.patch('model.model._execute', new=AsyncMock(return_value=("mock_output", "")))
    model = MagicMock(spec=Model)
    model.repository = MagicMock()
    return model

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
    mock_model.repository.repo.is_dirty = MagicMock(return_value=False)
    controller.create_commit()

    controller.view.display_notification.assert_has_calls([call("No changes")])

def test_generate_commit_with_changes(controller, mock_model):
    mock_model.repository.repo.is_dirty = MagicMock(return_value=True)
    mock_model.repository.repo.remotes = []

    def side_effect(prompt, options):
        if prompt == "Do you want stage all changes?":
            return "y"
        if prompt == "Do you want to push the commit to a remote?" and options == ["Yes (y)", "No (n)"]:
            return "n"
        return "n"


    controller.view.display_selection = MagicMock(side_effect=side_effect)
    controller.model.create_commit_message = MagicMock(return_value="commit message")
    controller.view.display_generated_commit = MagicMock(return_value="a")

    controller.create_commit()
    controller.model.create_commit_message.assert_called_once()

def test_generate_commit_higher_temperature(controller, mock_model):
    mock_model.repository.repo.is_dirty = MagicMock(return_value=True)
    mock_model.repository.repo.remotes = []

    def side_effect(prompt, options):
        if prompt == "Do you want stage all changes?":
            return "y"
        if prompt == "Do you want to push the commit to a remote?" and options == ["Yes (y)", "No (n)"]:
            return "n"
        return "n"


    controller.view.display_selection = MagicMock(side_effect=side_effect)
    controller.model.create_commit_message = MagicMock(return_value="commit message")
    controller.view.display_generated_commit = MagicMock(side_effect=["r", "a"])

    controller.create_commit()
    assert controller.model.create_commit_message.call_count == 2


def test_generate_commit_push_remote(controller, mock_model):
    mock_model.repository.repo.is_dirty = MagicMock(return_value=True)
    mock_remote1 = MagicMock(name="remote1")
    mock_remote1.name = "remote1"
    mock_remote2 = MagicMock(name="remote2")
    mock_remote2.name = "remote2"
    mock_remote3 = MagicMock(name="remote3")
    mock_remote3.name = "remote3"

    mock_model.repository.repo.remotes = [mock_remote1, mock_remote2, mock_remote3]

    loop_counter = 0

    def side_effect(prompt, options):
        nonlocal loop_counter
        if prompt == "Do you want stage all changes?":
            return "y"
        if prompt == "Do you want to push the commit to a remote?":
            return "y"
        if prompt == "Select a remote to push to:":
            if loop_counter == 0:
                loop_counter += 1
                return "remote1"
            elif loop_counter == 1:
                loop_counter += 1
                return "exit"
        return "n"


    controller.view.display_selection = MagicMock(side_effect=side_effect)
    controller.model.create_commit_message = MagicMock(return_value="commit message")
    controller.model.commit = MagicMock()
    controller.view.display_generated_commit = MagicMock(return_value="c")

    with patch.object(mock_remote1, 'push') as mock_push:
        controller.create_commit()

    controller.model.commit.assert_called_once()
    mock_push.assert_called_once()

