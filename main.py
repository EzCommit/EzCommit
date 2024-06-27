from .controller.controller import Controller
from .config import EZCommitConfig
import click

@click.command()
@click.option('--visual', is_flag = True, help = 'Visual commits history.')
@click.option('--context_path', help='Path to context file')
@click.option('--convention_path', help='Path to convention file')
@click.option('--gen-cmt', is_flag=True, help='hehe')
@click.option('--gen-pr', is_flag=True, help='hehe')
@click.option('--init', is_flag=True, help='hehe')
@click.option('--reinit', is_flag=True, help='hehe')
@click.option('--remove', is_flag=True, help='hehe')
def main(**kwargs):
    repo_path = EZCommitConfig.get_repo_path()
    print(repo_path)
    if kwargs.get('init'):
        if EZCommitConfig.is_initialized(repo_path):
            Controller.display_notification("Configuration already initialized.")
            exit(0)
            
        msg = EZCommitConfig.init_config(repo_path)
        Controller.display_notification(msg)
    elif kwargs.get('reinit'):
        msg = EZCommitConfig.reinit_config(repo_path)
        Controller.display_notification(msg)
        exit(0)
    elif kwargs.get('remove'):
        EZCommitConfig.remove_config(repo_path)
        Controller.display_notification("Ezcommit removed.")
        exit(0)

    try:
        loaded_config = EZCommitConfig.load_config(repo_path)
        controller = Controller(loaded_config)
    except FileNotFoundError:
        Controller.display_notification("No configuration file found. Please run `ezcommit --init` to initialize configuration.")

        exit(1)

    if kwargs.get('gen_cmt'):
        controller.create_commit()
    elif kwargs.get('visual'):
        controller.display_visual_log()
    elif kwargs.get('gen_pr'):
        controller.create_pull_request()
    else:
        controller.display_welcome_message()
        click.echo("Use --help for command options.")

    exit(0)
if __name__ == "__main__":
    main()
