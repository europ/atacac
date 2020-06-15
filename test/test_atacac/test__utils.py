import os
import sys
import yaml
import re
import pytest
import tempfile
from unittest import mock

import test.utils

from atacac import _utils

def test_log():
    pass

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
        pytest.param("Unsupported asset type 'Andromeda'!",
                     "Andromeda", ("label", 1), id="unsupported asset type")
    ]
)
@mock.patch("tower_cli.get_resource")
def test_tower_list(get_resource_mock, error, asset_type, query):
    result_assets = [{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}]

    get_resource_mock.return_value.list.return_value = {"results": result_assets}

    try:
        retval = _utils.tower_list(asset_type, query)
    except _utils.Error as e:
        assert e.message == error
        assert e.error_code == 1
    else:
        get_resource_mock.assert_called_with(asset_type)
        get_resource_mock.return_value.list.assert_called_with(all_pages=True, query=("label", 1))
        assert retval == result_assets

def test_tower_receive():
    pass

def test_tower_send():
    pass

@pytest.mark.parametrize(
    "error_regexp",
    [
        pytest.param(None, id="valid file path"),
        pytest.param("^Failed to read content of '[a-zA-Z0-9/]+'$", id="invalid file path")
    ]
)
def test_load_asset(error_regexp):
    if error_regexp:
        try:
            result = _utils.load_asset("/tmp/atacac/atacac/atacac/atacac/atacac")
        except _utils.Error as e:
            assert re.match(error_regexp, e.message)
            assert e.error_code == 1
    else:
        file_data = (
            "---\n"
            "key_a:\n"
            "  key_i: foo\n"
            "  key_j: 111\n"
            "key_b:\n"
            "  key_x: bar\n"
            "  key_y: 222\n"
        )

        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.write(bytes(file_data, encoding = 'utf-8'))
            tmpfile.seek(0)

            result = _utils.load_asset(tmpfile.name)

            assert result == yaml.safe_load(file_data)

