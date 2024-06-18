from view.view import View
from model.model import Model

class Controller:
    def __init__(self, ):
        self.view = View()
        self.model = Model()

    def display_diff(self):
        diffs = self.model.get_changes()
        self.view.display_diff(diffs)

    def create_commit(self):
        self.model.create_commit()
        # self.view.display_create_commit()

    def display_welcome_message(self):
        self.view.display_welcome_message()
        self.view.display_feature()

