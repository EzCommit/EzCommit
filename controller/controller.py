from view import View
from model import Model
from openai import AuthenticationError
from github import GithubException


class Controller:
    def __init__(self, config):
        self.view = View()
        self.model = Model(config)

    def display_diff(self):
        diffs = self.model.get_changes()
        self.view.display_diff(diffs)

    def create_pull_request(self):
        src_branch = self.model.get_current_branch()
        branches = self.model.list_all_branches()
        branches.remove(src_branch)
        while True: 
            dest_branch = self.view.display_selection("Which branch do you want to pull request into?", branches)

            if dest_branch == 'exit':
                return

            if dest_branch not in branches and not dest_branch.isdigit():
                self.view.display_notification("Invalid branch selected")
                continue

            if dest_branch.isdigit():
                if int(dest_branch) not in range(1, len(branches) + 1):
                    self.view.display_notification("Invalid branch selected")
                    continue
                dest_branch = branches[int(dest_branch) - 1]

            try:
                content, title = self.model.create_pr_content(src_branch, dest_branch)
            except AuthenticationError as e:
                self.view.display_error(e.body.get('message', 'Unknown error API'))
                if ("Incorrect API key provided" in e.body.get('message', '')):
                    print('Run ezcommit --api-key to set a new API key')
                return
            except Exception as e:
                self.view.display_error('Unknown error')
                return

            break

        repo_name = self.model.repository.get_repo_name()
        try:
            pr = self.model.create_pull_request(repo_name, src_branch, dest_branch, content, title)

            self.view.display_notification(f"Pull request created: {pr.html_url}")
        except AuthenticationError as e:
            self.view.display_error(e.body.get('message', 'Unknown error API'))
            if ("Incorrect API key provided" in e.body.get('message', '')):
                print('Run ezcommit --api-key to set a new API key')
            return
        except GithubException as e:
            self.view.display_error(e.data.get('errors', 'Unknown error')[0]['message'])
            return
        except Exception as e:
            self.view.display_error('Unknown error')
            return


    def create_commit(self):
        temperature = 0.8
        if self.model.repository.repo.is_dirty() or self.model.repository.repo.untracked_files:
            while True:
                select = self.view.display_selection("Do you want stage all changes?", ["Yes (y)", "No (n)"])

                try: 
                    if select == 'exit':
                        return
                    if select not in ['y', 'n']:
                        self.view.display_notification("Invalid selection")
                        continue
                    if select == 'n':
                        cmt_msg = self.model.create_commit_message(all_changes=False)
                        break
                    if select == 'y':
                        cmt_msg = self.model.create_commit_message(all_changes=True)
                        break

                except AuthenticationError as e:
                    self.view.display_error(e.body.get('message', 'Unknown error'))
                    if ("Incorrect API key provided" in e.body.get('message', '')):
                        print('Run ezcommit --api-key to set a new API key')
                    return
                except Exception as e:
                    self.view.display_error('Unknown error')
                    return


            while True:
                self.view.clear()
                select = self.view.display_generated_commit(cmt_msg)
                if select == 'a':
                    return
                
                if select == 'r':
                    temperature += 0.1
                    try:
                        cmt_msg = self.model.create_commit_message(all_changes=False, temperature=temperature)
                        continue
                    except Exception as e:
                        self.view.display_error(e.body.get('message', 'Unknown error'))

                
                if select == 'c': 
                    self.model.commit(cmt_msg)
                    break
        else: 
            self.view.display_notification("No changes")
            cmt_msg = "No changes"

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
                remote = remote_dict[select_remote].push(refspec=f'{self.model.get_current_branch()}:{self.model.get_current_branch()}')
                self.view.display_notification(f"Pushed to remote {select_remote}")
                break
            else:
                self.view.display_notification("Invalid remote selected")

    def display_welcome_message(self):
        self.view.display_welcome_message()

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

    @staticmethod
    def display_notification(msg):
        View.display_notification(msg)