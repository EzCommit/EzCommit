import os
import shutil
import json
from git import Repo, InvalidGitRepositoryError, NoSuchPathError
from view import View

class EZCommitConfig:
    CONFIG_DIR = ".ezcommit"
    CONFIG_FILE = "config.json"

    def __init__(self, repo_path, convention_path, db_path, openai_api_key, access_token):
        self.repo_path = repo_path
        self.convention_path = convention_path
        self.db_path = db_path
        self.openai_api_key = openai_api_key
        self.access_token = access_token

    def set_api_key():
        repo_path = EZCommitConfig.get_repo_path()
        openai_api_key = View.display_prompt("Enter your OpenAI API key", "Key")

        with open(os.path.join(repo_path, EZCommitConfig.CONFIG_DIR, EZCommitConfig.CONFIG_FILE), 'r') as config_file:
            config_data = json.load(config_file)
            config_data["OPENAI_API_KEY"] = openai_api_key

        with open(os.path.join(repo_path, EZCommitConfig.CONFIG_DIR, EZCommitConfig.CONFIG_FILE), 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

    def set_access_token():
        repo_path = EZCommitConfig.get_repo_path()
        access_token = View.display_prompt("Enter your GitHub access token", "Token")
        
        with open(os.path.join(repo_path, EZCommitConfig.CONFIG_DIR, EZCommitConfig.CONFIG_FILE), 'r') as config_file:
            config_data = json.load(config_file)
            config_data["ACCESS_TOKEN"] = access_token
        
        with open(os.path.join(repo_path, EZCommitConfig.CONFIG_DIR, EZCommitConfig.CONFIG_FILE), 'w') as config_file:
            json.dump(config_data, config_file, indent=4)


    @staticmethod
    def reinit_config():
        repo_path = EZCommitConfig.get_repo_path()
        config_path = os.path.join(repo_path, EZCommitConfig.CONFIG_DIR)
        if os.path.exists(config_path):
            shutil.rmtree(config_path)
        
        return EZCommitConfig.init_config(repo_path)

    @staticmethod
    def init_config():
        repo_path = EZCommitConfig.get_repo_path()
        config_path = os.path.join(repo_path, EZCommitConfig.CONFIG_DIR)
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        
        config_file_path = os.path.join(config_path, EZCommitConfig.CONFIG_FILE)

        api_key = View.display_prompt("Enter your OpenAI API key", "Key")
        access_token = View.display_prompt("Enter your GitHub access token\nYou can find it at: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens", "Token")
        
        config_data = {
            "REPO_PATH": repo_path,
            "CONVENTION_PATH": f"{repo_path}/.ezcommit/default_convention.txt",
            "DB_PATH": f"{repo_path}/.ezcommit/db",
            "OPENAI_API_KEY": api_key,
            "ACCESS_TOKEN": access_token,
        }
        
        with open(config_file_path, 'w') as config_file:
            json.dump(config_data, config_file, indent=4)
        
        
        src_default_convention = os.path.join(os.path.dirname(__file__), "helper", "default_convention.txt")
        dest_default_convention = os.path.join(config_path, "default_convention.txt")
        if os.path.exists(src_default_convention):
            shutil.copy(src_default_convention, dest_default_convention)
            print(f"Moved default_convention to {dest_default_convention}")
        else:
            print(f"File {src_default_convention} does not exist")

        return f"Configuration initialized and saved to {config_file_path}"

    @staticmethod
    def load_config():
        repo_path = EZCommitConfig.get_repo_path()
        config_path = os.path.join(repo_path, EZCommitConfig.CONFIG_DIR, EZCommitConfig.CONFIG_FILE)
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"No configuration file found at {config_path}")
        
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
        
        return EZCommitConfig(
            config_data["REPO_PATH"],
            config_data["CONVENTION_PATH"],
            config_data["DB_PATH"],
            config_data["OPENAI_API_KEY"],
            config_data["ACCESS_TOKEN"],
        )

    @staticmethod
    def remove_config(repo_path):
        repo_path = EZCommitConfig.get_repo_path()
        config_path = os.path.join(repo_path, EZCommitConfig.CONFIG_DIR)
        if os.path.exists(config_path):
            shutil.rmtree(config_path)
            return True
        return False

    @staticmethod
    def is_initialized():
        repo_path = EZCommitConfig.get_repo_path()
        config_path = os.path.join(repo_path, EZCommitConfig.CONFIG_DIR)
        config_file_path = os.path.join(config_path, EZCommitConfig.CONFIG_FILE)
        return os.path.exists(config_path) and os.path.exists(config_file_path)

    @staticmethod
    def get_repo_path():
        try:
            repo = Repo(os.getcwd(), search_parent_directories=True)
            return repo.git.rev_parse("--show-toplevel")
        except (InvalidGitRepositoryError, NoSuchPathError):
            View.display_error("Not a git repository")
            exit(1)


