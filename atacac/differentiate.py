import os
import json
import glob

import yaml
import dictdiffer
import click
from tower_cli.exceptions import TowerCLIError

from atacac._utils import log, tower_receive


@click.command()
@click.argument('assets_glob', envvar='ASSETS_GLOB')
def main(assets_glob):
    diff = False

    for file_name in glob.glob(assets_glob, recursive=True):
        try:
            jt_name = os.path.splitext(file_name)[0].replace('_', ' ')
            jt_data = tower_receive('job_template', jt_name)[0]
        except TowerCLIError:
            log('INFO', (f"Asset '{jt_name}' doesn't exist in Tower, no need "
                         "to check for diffs"))
            continue

        jt_file_src = file_name
        jt_file_src_data = yaml.load(open(jt_file_src), Loader=yaml.FullLoader)

        log('INFO', f"Differentiating '{jt_file_src}' and '{jt_name}'")

        differences = list(dictdiffer.diff(jt_data, jt_file_src_data))
        if differences != []:
            diff = True
            log('WARNING', (f"  Mismatch, '{jt_file_src}' is not the same as "
                            f"the '{jt_name}' in tower!"))
            log('INFO', "  Difference:")
            for diff in differences:
                for line in json.dumps(diff, indent=2).splitlines():
                    log('INFO', f"    {line}")

    if diff:
        log('ERROR', "Difference(s) found!", fatal=True)


if __name__ == "__main__":
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
