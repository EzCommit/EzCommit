from controller.controller import Controller
import click

@click.command()
@click.option('--diff', is_flag=True, help='Display git differences.')
@click.option('--create-commit', is_flag=True, help='Display git differences.')
def main(**kwargs):
    controller = Controller()
    if kwargs.get('diff'):
        controller.display_diff()
    elif kwargs.get('create_commit'):
        controller.create_commit()
    elif not any(kwargs.values()):
        controller.display_welcome_message()
    else:
        click.echo("Use --help for command options.")

if __name__ == "__main__":
    main()
