__all__ = [
    'tower_list',
    'tower_receive',
    'tower_send',
    'log',
]

import json
import textwrap

import click
import tower_cli
from tower_cli.cli.transfer.send import Sender
from tower_cli.cli.transfer.receive import Receiver
from tower_cli.cli.transfer.common import SEND_ORDER as ASSET_TYPES
import yaml


LOG_COLORS = {
    'INFO': 'white',
    'DEBUG': 'white',
    'WARNING': 'yellow',
    'ERROR': 'red',
}


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
