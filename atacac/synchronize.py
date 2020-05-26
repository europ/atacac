import glob

import click

from atacac._utils import log, tower_list, tower_receive, load_asset


@click.command()
@click.argument('label_id', envvar='LABEL_ID')
@click.argument('assets_glob', envvar='ASSETS_GLOB')
def main(label_id, assets_glob):
    # asset names in repository
    local_assets_jt = []
    local_assets_other = []
    for file_name in sorted(glob.glob(assets_glob, recursive=True)):
        asset = load_asset(file_name)
        # Can synchronize only assets of type job_template because we are
        # getting assets from tower by label. Label is not available on projects
        # or inventories.
        if asset['asset_type'] != 'job_template':
            local_assets_other.append({
                'name': asset['name'],
                'asset_type': asset['asset_type']
            })
        else:
            local_assets_jt.append(asset['name'])

    # asset names in tower
    tower_assets = []
    for item in tower_list('job_template', [('labels', label_id)]):
        asset = item
        asset.update({'data': tower_receive('job_template', item['name'])[0]})
        tower_assets.append(asset)

    common_assets = set(tower_assets).intersection(set([
        asset['name'] for asset in local_assets_jt
    ]))

    for asset in common_assets:
        log('INFO', f"'{asset}' located both in the repository and in the tower")

    # union without the intersection
    diff = set(tower_assets).symmetric_difference(set(local_assets_jt))

    error = False

    for asset in diff:
        if asset not in tower_assets:
            log('WARNING', f"'{asset}' not found in tower ... will be recreated")
        elif asset not in local_assets_jt:
            error = True
            log('ERROR', (f"'{asset}' not found in repository ... will be reported "
                          "(not allowed)"))

    for asset in tower_assets:
        try:
            inventory = asset['data']['inventory']
        except KeyError:
            pass
        else:
            for local_asset in local_assets_other:
                if local_asset['asset_type'] == 'inventory':
                    if inventory == local_asset['name']:
                        log('INFO', (f"'{inventory}' located both in the repository "
                                     "and in the tower"))
                    else:
                        error = True
                        log('ERROR', (f"'{inventory}' not found in repository ... will"
                                      "be reported (not allowed)"))

    if error:
        log('INFO', (
            "Investigate if the asset should be deleted from tower, "
            "added to the repository, or it's label removed."
        ))
        log('ERROR', "Reported error(s) are not permitted!", fatal=True)


if __name__ == "__main__":
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    main()
