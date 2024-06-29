import pytest
from unittest.mock import MagicMock, patch

from ..controller.controller import Controller
from ..config import EZCommitConfig
from github import GithubException
from openai import AuthenticationError

@pytest.fixture
def mock_config():
    config = MagicMock(spec=EZCommitConfig)
    config.repo_path = '/home/hoaithi/angular-project/meogroup-backend'
    config.db_path = '/home/hoaithi/angular-project/meogroup-backend/.ezcommit/db'
    return config

@pytest.fixture
def mock_model():
    model = MagicMock()
    model.get_current_branch.return_value = 'test'
    model.list_all_branches.return_value = ['main', 'test']
    model.repository.get_repo_name.return_value = 'meogroup-backend'

    return model

@pytest.fixture
def mock_view():
    view = MagicMock()
    return view

@pytest.fixture
def controller(mock_model, mock_view, mock_config):
    with patch('controller.controller.Model', return_value=mock_model):
        with patch('controller.controller.View', return_value=mock_view):
            with patch('config.EZCommitConfig.load_config', return_value=mock_config):
                return Controller(config=mock_config)

@patch('click.prompt')
def test_create_pull_request_success(mock_click_prompt, controller, mock_model, mock_view):
    # Arrange
    mock_model.create_pr_content.return_value = ('PR Content', 'PR Title')
    mock_model.create_pull_request.return_value = MagicMock(html_url='http://example.com/pr')
    mock_click_prompt.return_value = 'main'
    
    # Act
    controller.create_pull_request()

    # Assert
    mock_view.display_notification.assert_called_once()

    # Clean
    mock_model.reset_mock()
    mock_view.reset_mock()


@patch('click.prompt')
def test_create_pull_request_exit(mock_click_prompt, controller, mock_model, mock_view):
    # Arrange
    mock_view.display_selection.return_value = 'exit'
    
    # Act
    controller.create_pull_request()

    # Assert
    mock_view.display_notification.assert_not_called()
    mock_view.display_error.assert_not_called()
    mock_model.create_pr_content.assert_not_called()
    mock_model.create_pull_request.assert_not_called()

    # Clean
    mock_model.reset_mock()
    mock_view.reset_mock()

@patch('click.prompt')
def test_create_pull_request_invalid_branch(mock_click_prompt, controller, mock_model, mock_view):
    # Arrange
    mock_view.display_selection.side_effect = ['invalid_branch', 'exit']
    
    # Act
    controller.create_pull_request()

    # Assert
    mock_view.display_notification.assert_called_with("Invalid branch selected")

    # Clean
    mock_model.reset_mock()
    mock_view.reset_mock()

@patch('click.prompt')
def test_create_pull_request_valid_branch_as_digit(mock_click_prompt, controller, mock_model, mock_view):
    # Arrange
    mock_view.display_selection.side_effect = ['1', 'exit']
    
    # Act
    controller.create_pull_request()

    # Assert
    mock_model.create_pr_content.assert_called_once_with('test', 'main')
    mock_view.display_error.assert_called_once()

    # Clean
    mock_model.reset_mock()
    mock_view.reset_mock()

@patch('click.prompt')
def test_create_pull_request_github_exception(mock_click_prompt, controller, mock_model, mock_view):
    # Arrange
    error = GithubException(404, data={'errors': [{'message': 'GitHub error'}]})
    mock_model.create_pull_request.side_effect = error
    mock_view.display_selection.side_effect = ['main', 'exit']
    mock_model.create_pr_content.return_value = ('PR Content', 'PR Title')
    
    # Act
    controller.create_pull_request()

    # Assert
    mock_view.display_error.assert_called_with('GitHub error')

class MockAuthenticationError(Exception):
    def __init__(self, message, body=None):
        self.body = body or {'message': message}
        super().__init__(message)

@patch('click.prompt')
def test_create_pull_request_authentication_error(mock_click_prompt, controller, mock_model, mock_view):
    # Arrange
    error = MockAuthenticationError("Auth error", body={'message': 'Auth error'})
    mock_model.create_pr_content.side_effect = error
    mock_view.display_selection.side_effect = ['main', 'exit']
    
    # Act
    controller.create_pull_request()

    # Assert
    mock_view.display_error.assert_called_with('Unknown error')
    
    # Clean
    mock_model.reset_mock()
    mock_view.reset_mock()

@patch('click.prompt')
def test_create_pull_request_generic_exception(mock_click_prompt, controller, mock_model, mock_view):
    # Arrange
    mock_model.create_pr_content.side_effect = Exception("Unknown error")
    mock_view.display_selection.side_effect = ['main', 'exit']
    
    # Act
    controller.create_pull_request()

    # Assert
    mock_view.display_error.assert_called_with('Unknown error')
    
    # Clean
    mock_model.reset_mock()
    mock_view.reset_mock()


@patch('openai.AuthenticationError')
def test_create_pull_request_openai_api_key_error(mock_auth_error, controller, mock_model, mock_view):
    # Arrange
    error_instance = mock_auth_error
    mock_model.create_pr_content.side_effect = error_instance

    mock_view.display_selection.side_effect = ['main', 'exit']
    
    # Act
    controller.create_pull_request()

    # Assert
    mock_view.display_error.assert_called_with('Unknown error')
    
    # Clean
    mock_model.reset_mock()
    mock_view.reset_mock()
