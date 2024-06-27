import click
import re
import textwrap


def format_diff(diffs):
    formatted_diffs = []
    for line in diffs:
        clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
        formatted_diffs.append(clean_line)
    return "\n".join(formatted_diffs)

class View:
    def __init__(self):
        pass

    def display_diff(self, diffs):
        formatted_diffs = format_diff(diffs)
        self._display_with_frame(formatted_diffs, title="Git Diff Output")
        
    def display_welcome_message(self):
        welcome_lines = [
            "Welcome to ezCommit",
            "----------------------------------------",
            "Your easy commit solution for managing Git repositories.",
            "Type --help to see available commands."
        ]
        self._display_with_frame(welcome_lines, title="Welcome Message")

    @staticmethod
    def _display_with_frame(content_lines, title=""):
        if isinstance(content_lines, str):
            content_lines = content_lines.split('\n')
        top_bottom_border = '+' + '-' * 74 + '+'
        side_border = '|'
        max_line_length = 72  

        if title:
            title_line = f"{side_border} {title.center(max_line_length)} {side_border}"
            click.echo(top_bottom_border)
            click.echo(title_line)
            click.echo(top_bottom_border)  
        
        for line in content_lines:
            wrapped_lines = textwrap.wrap(line, width=max_line_length)
            for wrapped_line in wrapped_lines:
                formatted_line = f"{side_border} {wrapped_line.ljust(max_line_length)} {side_border}"
                click.echo(formatted_line)
        
        click.echo(top_bottom_border)    

    def display_generated_commit(self, msg):
        click.clear()
        if (msg == "No changes found"):
            click.echo(msg)
            return "a"
        
        self._display_with_frame(msg, title="Generated Commit")
        click.echo("")
        user_input = click.prompt("""Type c to commit, r to regenerate, a to abort""")
        return user_input

    def display_pull_requests(self, msg, title):
        click.clear()
        if (msg == "No changes found"):
            click.echo(msg)
            return "a"
        
        self._display_with_frame(msg, title)
        click.echo("")
        user_input = click.prompt("""Type c to create PRs, r to regenerate, a to abort""")
        return user_input

    def display_summarize(self, msg):
        click.clear()
        
        self._display_with_frame(msg, "Summarize Documentation")
        click.echo("")
        user_input = click.prompt("""Type c to export, r to regenerate, a to abort""")
        return user_input
    
    def display_visual_log(self, log_output):
        self._display_with_frame(log_output, title = "Commits History Visualization")

    def display_info(self, msg, title):
        self._display_with_frame(msg, title)

    def display_selection(self, question, options):
        message = ''
        for i, option in enumerate(options):
            message += f"{option}\n"

        options_str = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])

        self._display_with_frame(f"Option:\n{options_str}", question)
        user_input = click.prompt("Choose an option (type the number)")
        return user_input.strip()

    @staticmethod
    def display_notification(msg):
        click.clear()
        View._display_with_frame(msg, "Notification")

    @staticmethod
    def display_error(msg):
        click.clear()
        View._display_with_frame(msg, "Error Message")

    @staticmethod
    def display_prompt(msg, field):
        click.clear()
        View._display_with_frame(msg, "Input")
        return click.prompt(field)

    

    def clear(self):
        click.clear()
    