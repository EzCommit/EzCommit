from view.view import View
from model.git import GitModel

class Controller:
    def __init__(self, model_configs: dict):
        self.view = View()
        self.model = GitModel(**model_configs)

    def display_diff(self):
        diffs = self.model.get_changes()
        self.view.display_diff(diffs)

    def display_welcome_message(self):
        self.view.display_welcome_message()
        self.view.display_feature()
    
    def test(self):
        diffs = self.model.generate_commit()
        print(diffs)

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

    def display_visual_log(self):
        log_output = self.model.get_visual_log()
        self.view.display_visual_log(log_output)