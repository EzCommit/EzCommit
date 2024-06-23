from controller.controller import Controller
import click

@click.command()
@click.option('--diff', is_flag=True, help='Display git differences.')
@click.option('--gc', is_flag=True, help='Generate commit message')
@click.option('--visual', is_flag = True, help = 'Visual commits history.')
@click.option('--context_path', help='Path to context file')
@click.option('--convention_path', help='Path to convention file')
# @click.option('--create-commit', is_flag=True, help='Display git differences.')
def main(diff, gc, context_path, convention_path, visual):
    controller = Controller({'context_path': context_path, 'convention_path': convention_path})
    controller.display_welcome_message()
    if diff:
        controller.display_diff()
    elif gc:
        controller.generate_commit()
    elif visual:
        controller.display_visual_log()
    else:
        click.echo("Use --help for command options.")

if __name__ == "__main__":
    main()
