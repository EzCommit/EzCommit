import os
import shutil
import json
from git import Repo, InvalidGitRepositoryError, NoSuchPathError

class EZCommitConfig:
    CONFIG_DIR = ".ezcommit"
    CONFIG_FILE = "config.json"

    def __init__(self, repo_path, convention_path, db_path):
        self.repo_path = repo_path
        self.convention_path = convention_path
        self.db_path = db_path

    @staticmethod
    def reinit_config(repo_path):
        config_path = os.path.join(repo_path, EZCommitConfig.CONFIG_DIR)
        if os.path.exists(config_path):
            shutil.rmtree(config_path)
        
        return EZCommitConfig.init_config(repo_path)

    @staticmethod
    def init_config(repo_path):
        config_path = os.path.join(repo_path, EZCommitConfig.CONFIG_DIR)
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        
        config_file_path = os.path.join(config_path, EZCommitConfig.CONFIG_FILE)
        
        config_data = {
            "REPO_PATH": repo_path,
            "CONVENTION_PATH": f"{repo_path}/.ezcommit/default_convention.txt",
            "DB_PATH": f"{repo_path}/.ezcommit/db"
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
    def load_config(repo_path):
        config_path = os.path.join(repo_path, EZCommitConfig.CONFIG_DIR, EZCommitConfig.CONFIG_FILE)
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"No configuration file found at {config_path}")
        
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
        
        return EZCommitConfig(
            config_data["REPO_PATH"],
            config_data["CONVENTION_PATH"],
            config_data["DB_PATH"]
        )

    @staticmethod
    def remove_config(repo_path):
        config_path = os.path.join(repo_path, EZCommitConfig.CONFIG_DIR)
        if os.path.exists(config_path):
            shutil.rmtree(config_path)
            return True
        return False

    @staticmethod
    def is_initialized(repo_path):
        config_path = os.path.join(repo_path, EZCommitConfig.CONFIG_DIR)
        config_file_path = os.path.join(config_path, EZCommitConfig.CONFIG_FILE)
        return os.path.exists(config_path) and os.path.exists(config_file_path)

    @staticmethod
    def get_repo_path():
        try:
            repo = Repo(os.getcwd(), search_parent_directories=True)
            return repo.git.rev_parse("--show-toplevel")
        except (InvalidGitRepositoryError, NoSuchPathError):
            raise Exception("Current directory is not a valid git repository.")

