import glob

import click

from atacac._utils import log, tower_list, load_asset


@click.command()
@click.argument('label_id', envvar='LABEL_ID')
@click.argument('assets_glob', envvar='ASSETS_GLOB')
def main(label_id, assets_glob):
    # asset names in repository
    local_assets = []
    for file_name in sorted(glob.glob(assets_glob, recursive=True)):
        asset = load_asset(file_name)
        # Can synchronize only assets of type job_template because we are
        # getting assets from tower by label. Label is not available on projects
        # or inventories.
        if asset['asset_type'] != 'job_template':
            continue
        local_assets.append(asset['name'])

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
