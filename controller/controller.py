from view.view import View
from model.model import Model

class Controller:
    def __init__(self, model_configs: dict):
        self.view = View()
        self.model = Model(**model_configs)

    def display_diff(self):
        diffs = self.model.get_changes()
        self.view.display_diff(diffs)

    def create_commit(self):
        temperature = 0.8
        if self.model.repository.repo.is_dirty():
            select = self.view.display_selection("Do you want stage all changes?", ["Yes (y)", "No (n)"])
            if select == 'n':
                cmt_msg = self.model.create_commit_message(all_changes=False)
            if select == 'y':
                cmt_msg = self.model.create_commit_message(all_changes=True)

            while True:
                select = self.view.display_generated_commit(cmt_msg)
                if select == 'a':
                    return
                
                if select == 'r':
                    temperature += 0.1
                    cmt_msg = self.model.create_commit_message(all_changes=False, temperature=temperature)
                    continue
                
                if select == 'c': 
                    self.model.commit(cmt_msg)
                    return
        else: 
            self.view.display_notification("No changes")

        remotes = self.model.repository.repo.remotes
        remote_names = [remote.name for remote in remotes]

        remote_dict = {}
        for remote in remotes:
            remote_dict[remote.name] = remote
            
        if not remote_names:
            self.view.display_notification("No remotes available")
            return

        while True:
            select = self.view.display_selection("Do you want to push the commit to a remote?", ["Yes (y)", "No (n)"])
            if select == 'exit':
                return
            
            if select != 'n' and select != 'y':
                self.view.display_notification("Invalid selected")
                continue
            else:
                break

        if select == 'n':
            return
        
        while True:
            select_remote = self.view.display_selection("Select a remote to push to:", remote_names)
            if select_remote == 'exit':
                return

            if select_remote in remote_names:
                self.view.display_notification(f"Pushed to remote {select_remote}")
                remote_dict[select_remote].push()
                break
            else:
                self.view.display_notification("Invalid remote selected")

    def display_welcome_message(self):
        self.view.display_welcome_message()
        self.view.display_feature()

    def generate_commit(self):
        temperature = 0.8

        msg = self.model.generate_commit(temperature)
        user_input = self.view.display_generated_commit(msg)

        while (user_input == "r"):
            temperature += 0.01
            msg = self.model.generate_commit(temperature)
            user_input = self.view.display_generated_commit(msg)

        if (user_input == "a"):
            return
        
        if (user_input == "c"):
            self.model.commit(msg)

    def create_commit_fast(self):
        temperature = 0.8
        if self.model.repository.repo.is_dirty():
            select = self.view.display_selection("Do you want stage all changes?", ["Yes (y)", "No (n)"])
            if select == 'n':
                cmt_msg = self.model.generate_commit(stages=False, temperature=temperature)
            if select == 'y':
                cmt_msg = self.model.generate_commit(stages=True, temperature=temperature)

            while True:
                select = self.view.display_generated_commit(cmt_msg)
                if select == 'a':
                    return
                
                if select == 'r':
                    temperature += 0.1
                    cmt_msg = self.model.create_commit_message(all_changes=False, temperature=temperature)
                    continue
                
                if select == 'c': 
                    self.model.commit(cmt_msg)
                    return
        else: 
            self.view.display_notification("No changes")

    def display_visual_log(self):
        log_output = self.model.get_visual_log()
        self.view.display_visual_log(log_output)