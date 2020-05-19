import os
import glob

import click

from atacac._utils import log, tower_list


@click.command()
@click.argument('label_id', envvar='LABEL_ID')
@click.argument('assets_glob', envvar='ASSETS_GLOB')
def main(label_id, assets_glob):
    # asset names in repository
    local_assets = [
        os.path.splitext(os.path.basename(file_name))[0].replace('_', ' ')
        for file_name in glob.glob(assets_glob, recursive=True)
    ]

    # asset names in tower
    tower_assets = [
        item['name']
        for item in tower_list('job_template', [('labels', label_id)])
    ]

    common_assets = set(tower_assets).intersection(set(local_assets))

    for asset in common_assets:
        log('INFO', f"'{asset}' located both in the repository and in the tower")

    # symmetric difference == disjunctive union == union without the intersection
    diff = set(tower_assets).symmetric_difference(set(local_assets))

    error = False
    for asset in diff:
        if asset not in tower_assets:
            log('WARNING', f"'{asset}' not found in tower ... will be recreated")
        elif asset not in local_assets:
            error = True
            log('ERROR', (f"'{asset}' not found in repository ... will be reported "
                          "(not allowed)"))

    if error:
        log('INFO', (
            "Investigate if the asset should be deleted from tower, "
            "added to the repository, or it's label removed."
        ))
        log('ERROR', "Reported error(s) are not permitted!", fatal=True)


if __name__ == "__main__":
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
