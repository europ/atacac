import re
import tempfile
import textwrap
from unittest import mock

import click
import pytest
import yaml

from atacac import _utils


@pytest.mark.parametrize(
    "level, fatal",
    [
        pytest.param("info", True, id="level='info', fatal"),
        pytest.param("INFO", True, id="level='INFO', fatal"),
        pytest.param("info", False, id="level='info'"),
        pytest.param("INFO", False, id="level='INFO'"),

        pytest.param("warn", True, id="level='warn', fatal"),
        pytest.param("WARN", True, id="level='WARN', fatal"),
        pytest.param("warn", False, id="level='warn'"),
        pytest.param("WARN", False, id="level='WARN'"),

        pytest.param("warning", True, id="level='warning', fatal"),
        pytest.param("WARNING", True, id="level='WARNING', fatal"),
        pytest.param("warning", False, id="level='warning'"),
        pytest.param("WARNING", False, id="level='WARNING'"),

        pytest.param("error", True, id="level='error', fatal"),
        pytest.param("ERROR", True, id="level='ERROR', fatal"),
        pytest.param("error", False, id="level='error'"),
        pytest.param("ERROR", False, id="level='ERROR'"),

        pytest.param("debug", True, id="level='debug', fatal"),
        pytest.param("DEBUG", True, id="level='DEBUG', fatal"),
        pytest.param("debug", False, id="level='debug'"),
        pytest.param("DEBUG", False, id="level='DEBUG'"),
    ]
)
@mock.patch("atacac._utils.textwrap")
@mock.patch("atacac._utils.click")
def test_log(mock_click, mock_textwrap, level, fatal):
    message = "This is a message."

    mock_click.Abort = click.Abort
    mock_click.style.return_value = level
    mock_textwrap.indent.return_value = f"{level} {message}"

    try:
        _utils.log(level, message, fatal=fatal)
        mock_click.echo.assert_called_once()
        mock_click.echo.assert_called_with(f"{level} {message}")
    except click.Abort:
        assert fatal is True


@pytest.mark.parametrize(
    "error, asset_type, query",
    [
        pytest.param(None, "user", ("label", 1), id="user"),
        pytest.param(None, "organization", ("label", 1), id="organization"),
        pytest.param(None, "team", ("label", 1), id="team"),
        pytest.param(None, "credential_type", ("label", 1), id="credential_type"),
        pytest.param(None, "credential", ("label", 1), id="credential"),
        pytest.param(None, "notification_template", ("label", 1), id="notification_template"),
        pytest.param(None, "inventory_script", ("label", 1), id="inventory_script"),
        pytest.param(None, "project", ("label", 1), id="project"),
        pytest.param(None, "inventory", ("label", 1), id="inventory"),
        pytest.param(None, "job_template", ("label", 1), id="job_template"),
        pytest.param(None, "workflow", ("label", 1), id="workflow"),
        pytest.param("Unsupported asset type 'ABC123XYZ'!",
                     "ABC123XYZ", ("label", 1), id="unsupported asset type")
    ]
)
@mock.patch("tower_cli.get_resource")
def test_tower_list(mock_get_resource, error, asset_type, query):
    result_assets = [{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}]

    mock_instance = mock_get_resource.return_value
    mock_instance.list.return_value = {"results": result_assets}

    try:
        retval = _utils.tower_list(asset_type, query)
    except _utils.Error as e:
        assert str(e) == error
        assert e.error_code == 1
    else:
        mock_get_resource.assert_called_once()
        mock_get_resource.assert_called_with(asset_type)

        mock_instance.list.assert_called_once()
        mock_instance.list.assert_called_with(all_pages=True, query=("label", 1))

        assert retval == result_assets


@mock.patch("atacac._utils.tower_receive")
@mock.patch("atacac._utils.tower_list")
def test_tower_list_all(mock_tower_list, mock_tower_receive):
    def tower_list(asset_type, query):
        return [{'id': 1, 'name': f'Example {asset_type}'}]

    mock_tower_list.side_effect = tower_list
    mock_tower_receive.return_value = [
        {
            'project': 'Example project',
            'inventory': 'Example inventory',
        },
    ]

    result = _utils.tower_list_all([('label', 1)])

    assert list(sorted(result, key=lambda i: i['name'])) == [
        {'id': 1, 'type': 'inventory', 'name': 'Example inventory'},
        {'id': 1, 'type': 'job_template', 'name': 'Example job_template'},
        {'id': 1, 'type': 'project', 'name': 'Example project'},
    ]

    mock_tower_list.assert_has_calls([
        mock.call('job_template', [('label', 1)]),
        mock.call('project', [('name', 'Example project')]),
        mock.call('inventory', [('name', 'Example inventory')]),
    ])


@pytest.mark.parametrize(
    "error, asset_type, asset_name",
    [
        pytest.param(None, "user", "file", id="user"),
        pytest.param(None, "organization", "file", id="organization"),
        pytest.param(None, "team", "file", id="team"),
        pytest.param(None, "credential_type", "file", id="credential_type"),
        pytest.param(None, "credential", "file", id="credential"),
        pytest.param(None, "notification_template", "file", id="notification_template"),
        pytest.param(None, "inventory_script", "file", id="inventory_script"),
        pytest.param(None, "project", "file", id="project"),
        pytest.param(None, "inventory", "file", id="inventory"),
        pytest.param(None, "job_template", "file", id="job_template"),
        pytest.param(None, "workflow", "file", id="workflow"),
        pytest.param("Unsupported asset type 'ABC123XYZ'!",
                     "ABC123XYZ", "file", id="unsupported asset type")
    ]
)
@mock.patch("atacac._utils.Receiver")
def test_tower_receive(mock_Receiver, error, asset_type, asset_name):
    dictionary = {"dictA": {"key_1": "value_1"}, "dictB": {"key_2": "value_2"}}

    mock_instance = mock_Receiver.return_value
    mock_instance.export_assets.return_value = dictionary

    try:
        assert _utils.tower_receive(asset_type, asset_name) == dictionary
    except _utils.Error as e:
        assert str(e) == error
        assert e.error_code == 1
    else:
        mock_Receiver.assert_called_once()

        mock_instance.export_assets.assert_called_once()
        mock_instance.export_assets.assert_called_with(all=False, asset_input={asset_type: [asset_name]})


@pytest.mark.parametrize(
    "assets",
    [
        pytest.param("foo", id="file"),
        pytest.param(["foo", "bar"], id="file list"),
    ]
)
@mock.patch("atacac._utils.Sender")
def test_tower_send(mock_Sender, assets):
    mock_instance = mock_Sender.return_value

    _utils.tower_send(assets)

    mock_Sender.assert_called_once()
    mock_Sender.assert_called_with(False)

    mock_instance.send.assert_called_once()
    mock_instance.send.assert_called_with(
        assets if isinstance(assets, list) else [assets], None, None, "default")


def test_load_asset_valid_path():
    file_data = textwrap.dedent(
        """\
        ---
        key_a:
          key_i: foo
          key_j: 111
        key_b:
          key_x: bar
          key_y: 222
        """
    )

    with tempfile.NamedTemporaryFile() as tmpfile:
        tmpfile.write(bytes(file_data, encoding="utf-8"))
        tmpfile.seek(0)

        result = _utils.load_asset(tmpfile.name)

        assert result == yaml.safe_load(file_data)


def test_load_asset_invalid_path():
    try:
        _utils.load_asset("./a/b/c/d/e/f/g/h/i/file")
    except _utils.Error as e:
        assert re.match(r"^Failed to read content of '\./a/b/c/d/e/f/g/h/i/file'$", str(e))
        assert e.error_code == 1
