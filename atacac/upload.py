import glob

import click

from atacac._utils import tower_send


@click.command()
@click.argument('assets_glob', envvar='ASSETS_GLOB')
def main(assets_glob):
    tower_send(glob.glob(assets_glob, recursive=True))


if __name__ == '__main__':
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
