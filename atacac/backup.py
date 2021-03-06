import os
import glob

import yaml
import click
from tower_cli.exceptions import TowerCLIError

from atacac._utils import log, load_asset, tower_receive, sanitize_filename


class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(Dumper, self).increase_indent(flow, False)


@click.command()
@click.argument('destination', envvar='BACKUP_PATH')
@click.argument('assets_glob', envvar='ASSETS_GLOB')
def main(destination, assets_glob):
    """
    Make backup of the Tower configuration.
    \f
    Download the actual Tower assets that are marked by a specific label from
    tower to a folder.

    !! ASSETS_GLOB must be in single quotes to prevent glob pattern expansion in
    shell.

    \b
    Folloving arguments can be passed via environment variables:
        * BACKUP_PATH
        * ASSETS_GLOB
    """
    try:
        os.makedirs(destination, exist_ok=True)
    except OSError:
        log('ERROR', f"Directory path: {destination}")
        log('ERROR', "Failed to create directory!", fatal=True)

    for file_name in sorted(glob.glob(assets_glob, recursive=True)):
        asset = load_asset(file_name)

        try:
            log('INFO', f"Downloading '{asset['name']}' ...")
            asset_data = tower_receive(asset['asset_type'], asset['name'])[0]
        except TowerCLIError:
            log('INFO', (f"... asset '{asset['name']}' does not exist in Tower"))
            continue

        file_path = os.path.join(
            destination,
            sanitize_filename(f'{asset_data["name"]}.{asset_data["asset_type"]}.yml')
        )

        file_content = yaml.dump(asset_data, Dumper=Dumper, default_flow_style=False)

        try:
            log('INFO', f"    File path: {file_path}")
            with open(file_path, 'w') as file:
                file.write("---\n")
                file.write(file_content)
        except EnvironmentError:
            log('ERROR', "Failed to write to the file!", fatal=True)

        log('INFO', "... downloaded")


if __name__ == "__main__":
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
