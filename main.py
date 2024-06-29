from .controller.controller import Controller
from .config import EZCommitConfig
import click

@click.command()
@click.option('--visual', is_flag = True, help = 'Visual commits history.')
@click.option('--context-path', help='Path to context file')
@click.option('--convention-path', is_flag=True, help='Path to convention file')
@click.option('--gen-cmt', is_flag=True, help='Generate commit message.')
@click.option('--gen-pr', is_flag=True, help='Generate pull request.')
@click.option('--init', is_flag=True, help='Initialize configuration.')
@click.option('--reinit', is_flag=True, help='Reinitialize configuration.')
@click.option('--remove', is_flag=True, help='Remove configuration.')
@click.option('--api-key', is_flag=True, help='Set OpenAI API key.')
@click.option('--sum', is_flag=True, help='Summarize changes.')
@click.option('-fast', is_flag=True, help='Use fast-mode for generation')
def main(**kwargs):
    if kwargs.get('init'):
        if EZCommitConfig.is_initialized():
            Controller.display_notification("Configuration already initialized.")
            exit(0)
            
        msg = EZCommitConfig.init_config()
        Controller.display_notification(msg)
    elif kwargs.get('reinit'):
        msg = EZCommitConfig.reinit_config()
        Controller.display_notification(msg)
        exit(0)
    elif kwargs.get('remove'):
        EZCommitConfig.remove_config()
        Controller.display_notification("Ezcommit removed.")
        exit(0)
    elif kwargs.get('api_key'):
        EZCommitConfig.set_api_key()
        exit(0)
    elif kwargs.get('convention_path'):
        EZCommitConfig.set_convention_path()
        exit(0)
    elif kwargs.get('context_path'):
        EZCommitConfig.set_context_path()
        exit(0)

    try:
        loaded_config = EZCommitConfig.load_config()
        controller = Controller(loaded_config)
    except FileNotFoundError:
        Controller.display_notification("No configuration file found. Please run `ezcommit --init` to initialize configuration.")

        exit(1)

    if kwargs.get('gen_cmt'):
        if kwargs.get('fast'):
            controller.create_commit_fast()
        else:
            controller.create_commit()
    elif kwargs.get('visual'):
        controller.display_visual_log()
    elif kwargs.get('sum'):
        controller.summarize()
    elif kwargs.get('gen_pr'):
        controller.create_pull_request()
    else:
        controller.display_welcome_message()
        click.echo("Use --help for command options.")

    exit(0)
if __name__ == "__main__":
    main()
