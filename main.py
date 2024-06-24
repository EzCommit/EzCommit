from controller.controller import Controller
import click

@click.command()
@click.option('--visual', is_flag = True, help = 'Visual commits history.')
@click.option('--context_path', help='Path to context file')
@click.option('--convention_path', help='Path to convention file')
@click.option('--gen-cmt', is_flag=True, help='Display git differences.')
def main(**kwargs):
    controller = Controller({'context_path': kwargs.get('context_path'), 'convention_path': kwargs.get('convention_path')})
    if kwargs.get('gen_cmt'):
        controller.create_commit()
    elif kwargs.get('--visual'):
        controller.display_visual_log()
    else:
        controller.display_welcome_message()
        click.echo("Use --help for command options.")

    exit(0)
if __name__ == "__main__":
    main()
