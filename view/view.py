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

    def display_feature(self):
        feature_lines = [
            "1. Create pull requests."
        ]
        self._display_with_frame(feature_lines, "Feature")
        
    def display_welcome_message(self):
        welcome_lines = [
            "Welcome to \x1b[1;32mezCommit\x1b[0m!",
            "----------------------------------------",
            "Your easy commit solution for managing Git repositories.",
            "Type --help to see available commands."
        ]
        self._display_with_frame(welcome_lines, title="Welcome Message")

    def _display_with_frame(self, content_lines, title=""):
        if isinstance(content_lines, str):
            content_lines = content_lines.split('\n')
        top_bottom_border = '+' + '-' * 74 + '+'
        side_border = '|'
        max_line_length = 72  

        if title:
            title_line = f"{side_border} {title.center(max_line_length)} {side_border}"
            header_footer_border = '+' + '-' * 74 + '+'

        click.echo(header_footer_border)
        if title:
            click.echo(title_line)
            click.echo(header_footer_border)  
        
        for line in content_lines:
            wrapped_lines = textwrap.wrap(line, width=max_line_length)
            for wrapped_line in wrapped_lines:
                formatted_line = f"{side_border} {wrapped_line.ljust(max_line_length)} {side_border}"
                click.echo(formatted_line)
        
        click.echo(top_bottom_border)    