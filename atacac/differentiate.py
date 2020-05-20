import json
import glob

import dictdiffer
import click
from tower_cli.exceptions import TowerCLIError
import yaml

from atacac._utils import log, tower_receive, load_asset


@click.command()
@click.argument('assets_glob', envvar='ASSETS_GLOB')
def main(assets_glob):
    diff = False

    for file_name in sorted(glob.glob(assets_glob, recursive=True)):
        asset = load_asset(file_name)

        try:
            jt_data = tower_receive(asset['asset_type'], asset['name'])[0]
        except TowerCLIError:
            log('INFO', (f"Asset '{asset['name']}' doesn't exist in Tower, no "
                         "need to check for diffs"))
            continue

        # Need to parse extra vars to dict becuse in assets file it is YAML and
        # in reponse from tower it is JSON.
        asset['extra_vars'] = yaml.safe_load(asset['extra_vars'])
        jt_data['extra_vars'] = yaml.safe_load(jt_data['extra_vars'])

        log('INFO', f"Differentiating '{file_name}' and '{asset['name']}'")
        differences = list(dictdiffer.diff(jt_data, asset))
        if differences != []:
            diff = True
            log('WARNING', (f"  Mismatch, '{file_name}' is not the same as "
                            f"the '{asset['name']}' in tower!"))
            log('INFO', "  Difference:")
            for d in differences:
                log('INFO', "    " + json.dumps(d, indent=2))

    if diff:
        log('ERROR', "Difference(s) found!", fatal=True)


if __name__ == "__main__":
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
