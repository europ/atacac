import os

import click
import yaml
from tower_cli.exceptions import TowerCLIError

from atacac._utils import log, tower_list_all, tower_receive, sanitize_filename


class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(Dumper, self).increase_indent(flow, False)


@click.command()
@click.argument('label_id', envvar='LABEL_ID')
@click.argument('destination', envvar='BACKUP_PATH')
def main(label_id, destination):
    """
    Download all job templates with label including dependencies.
    \f
    Download the actual Tower assets including dependencies (project and
    inventory) that are marked by a specific label from tower to a folder.

    \b
    Folloving arguments can be passed via environment variables:
        * BACKUP_PATH
        * LABEL_ID
    """
    try:
        os.makedirs(destination, exist_ok=True)
    except OSError:
        log('ERROR', f"Directory path: {destination}")
        log('ERROR', "Failed to create directory!", fatal=True)

    for asset in tower_list_all([('labels', label_id)]):
        try:
            log('INFO', f"Downloading '{asset['name']}' of type {asset['type']} ...")
            asset_data = tower_receive(asset['type'], asset['name'])[0]
        except TowerCLIError as e:
            log('INFO', (f"... failed: {e}"))
            continue

        file_path = os.path.join(
            destination,
            sanitize_filename(f'{asset["name"]}.{asset["type"]}.yml')
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
