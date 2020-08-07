__all__ = [
    'tower_list',
    'tower_receive',
    'tower_send',
    'log',
]

import json
import textwrap
import re

import click
import tower_cli
from tower_cli.cli.transfer.send import Sender
from tower_cli.cli.transfer.receive import Receiver
from tower_cli.cli.transfer.common import SEND_ORDER as ASSET_TYPES
import yaml
from dogpile.cache import make_region


LOG_COLORS = {
    'INFO': 'white',
    'DEBUG': 'white',
    'WARNING': 'yellow',
    'ERROR': 'red',
}


cache = make_region().configure(
    'dogpile.cache.memory'
)


class Error(Exception):
    def __init__(self, message, error_code=1):
        self.message = message
        self.error_code = error_code


def log(level, message, fatal=False):
    """
    Print mesage prefixed with styled log level (eg. ERROR will be red).

    Arguments:
        level (str) -- INFO | DEBUG | WARNING | ERROR
    """

    level = level.upper()
    if level == 'WARN':
        level = 'WARNING'

    level_styled = click.style(level, fg=LOG_COLORS.get(level), bold=fatal)
    message_styled = textwrap.indent(message, level_styled + '  ',
                                     predicate=lambda _: True)

    click.echo(message_styled)
    if fatal:
        raise click.Abort


@cache.cache_on_arguments()
def tower_list(asset_type, query):
    """
    List all assets of certain type in Tower.

    Arguments:
        asset_type -- asset type, eg. job_template
        query -- search query, list of tuples (key, value) where the value is
            the ID e.g. label=3SN is label=1

    Returns:
        list of assets as a dict {id: ..., name: ...}

    """
    if asset_type not in ASSET_TYPES:
        raise Error(f"Unsupported asset type '{asset_type}'!")

    resource = tower_cli.get_resource(asset_type)

    return [
        {
            'id': item['id'],
            'name': item['name']
        }
        for item in resource.list(all_pages=True, query=query)['results']
    ]


@cache.cache_on_arguments()
def tower_list_all(query):
    """
    Find all assets including dependencies; job templates with provided label_id
    and related projects and inventories.

    Arguments:
        label_id -- label ID

    Returns:
        list of assets as a dict {id: ..., type: ..., name: ...}
    """
    dependencies_types = ['project', 'inventory']
    # set of tuple(type, id, name)
    assets_set = set()

    for item in tower_list('job_template', query):
        assets_set.add(('job_template', item['id'], item['name']))

        for asset_data in tower_receive('job_template', item['name']):
            for dep_type in dependencies_types:
                for dep_data in tower_list(dep_type, [('name', asset_data[dep_type])]):
                    assets_set.add((dep_type, dep_data['id'], dep_data['name']))

    return [{'id': id, 'type': type, 'name': name} for type, id, name in assets_set]


@cache.cache_on_arguments()
def tower_receive(asset_type, asset_name):
    """
    Receive assets from Tower

    Arguments:
        asset_type -- asset type, eg. job_template
        asset_name

    Returns:
        assets objects
    """
    if asset_type not in ASSET_TYPES:
        raise Error(f"Unsupported asset type '{asset_type}'!")

    to_export = {asset_type: [asset_name]}

    receiver = Receiver()
    assets = receiver.export_assets(all=False, asset_input=to_export)

    # recursively convert OrderedDict to Dict
    # source: https://stackoverflow.com/a/27373073
    return json.loads(json.dumps(assets))


def tower_send(asset):
    """
    Upload assets to Tower.

    Arguments:
        asset -- asset object or list of assets objects
    """
    source = asset if isinstance(asset, list) else [asset]

    sender = Sender(False)
    sender.send(source, None, None, 'default')


def load_asset(file_path):
    """
    Load asset file to dict.

    Now simply opens file and parses YAML.
    """
    try:
        with open(file_path) as f:
            return yaml.safe_load(f)
    except IOError:
        raise Error(f"Failed to read content of '{file_path}'")


def sanitize_filename(filename):
    """
    Sanitize filename so it contains only alphanumeric characters, dot,
    underscore or dash. All other characters are replaced with single
    underscore and multiple consecutive uderscores is collapsed into one (eg.
    `a_%$#@_b` -> `a_b`).
    """
    return re.sub(r'[^a-zA-Z0-9.-]+', '_', filename)
