from controller.controller import Controller
import click

@click.command()
@click.option('--diff', is_flag=True, help='Display git differences.')
@click.option('--gc', is_flag=True, help='Generate commit message')
# @click.option('--create-commit', is_flag=True, help='Display git differences.')
def main(diff, gc):
    controller = Controller()
    controller.display_welcome_message()
    if diff:
        controller.display_diff()
    elif gc:
        controller.generate_commit()
    else:
        click.echo("Use --help for command options.")

if __name__ == "__main__":
    main()
