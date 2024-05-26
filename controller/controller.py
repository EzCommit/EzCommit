from view.view import View
from model.git import GitModel

class Controller:
    def __init__(self, ):
        self.view = View()
        self.model = GitModel()

    def display_diff(self):
        diffs = self.model.get_changes()
        self.view.display_diff(diffs)

    def display_welcome_message(self):
        self.view.display_welcome_message()
        self.view.display_feature()

