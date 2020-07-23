import glob

import click

from atacac._utils import tower_send


@click.command()
@click.argument('assets_glob', envvar='ASSETS_GLOB')
def main(assets_glob):
    """
    Upload assets to Tower.
    \f
    Rewrite the corresponding Ansible Tower assets with repository assets.

    !! ASSETS_GLOB must be in single quotes to prevent glob pattern expansion in
    shell.

    \b
    Folloving arguments can be passed via environment variables:
        * ASSETS_GLOB
    """
    tower_send(sorted(glob.glob(assets_glob, recursive=True)))


if __name__ == '__main__':
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
