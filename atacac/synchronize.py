import glob

import click

from atacac._utils import log, tower_list_all, load_asset


@click.command()
@click.argument('label_id', envvar='LABEL_ID')
@click.argument('assets_glob', envvar='ASSETS_GLOB')
def main(label_id, assets_glob):
    """
    Check for missing assets.
    \f
    Check if the repository's assets exits in Tower under a specific label and
    vice versa.

    !! ASSETS_GLOB must be in single quotes to prevent glob pattern expansion in
    shell.

    \b
    Folloving arguments can be passed via environment variables:
        * LABEL_ID
        * ASSETS_GLOB
    """
    # list of asset type+name in repository
    local_assets = []
    for file_name in sorted(glob.glob(assets_glob, recursive=True)):
        asset = load_asset(file_name)
        local_assets.append((asset['asset_type'], asset['name']))

    # list of asset type+name in tower
    tower_assets = [
        (item['type'], item['name'])
        for item in tower_list_all([('labels', label_id)])
    ]

    common_assets = set(tower_assets).intersection(set(local_assets))

    for asset_type, asset_name in common_assets:
        log('INFO', (f"'{asset_name}' of type {asset_type} located both in the "
                     "repository and in the tower"))

    # symmetric difference == disjunctive union == union without the intersection
    diff = set(tower_assets).symmetric_difference(set(local_assets))

    error = False
    for asset in diff:
        asset_type, asset_name = asset
        if asset not in tower_assets:
            log('WARNING', (f"'{asset_name}' of type {asset_type} not found in "
                            "tower ... will be recreated"))
        elif asset not in local_assets:
            error = True
            log('ERROR', (f"'{asset_name}' of type {asset_type} not found in "
                          "repository ... will be reported (not allowed)"))

    if error:
        log('INFO', (
            "Investigate if the asset should be deleted from tower, "
            "added to the repository, or it's label removed."
        ))
        log('ERROR', "Reported error(s) are not permitted!", fatal=True)


if __name__ == "__main__":
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
