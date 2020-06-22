import os
import re
from unittest import mock
from test.utils import MockDir

import pytest  # pylint: disable=import-error
from click.testing import CliRunner
from tower_cli.exceptions import TowerCLIError

from atacac import differentiate


assets = {
    "similar": ["A", "B", "C"],
    "different": ["M", "N", "O"],
    "missing": ["X", "Y", "Z"]
}


@pytest.mark.parametrize(
    "assets_glob, assets",
    [
        pytest.param("prefix*", assets, id="match prefix"),
        pytest.param("*.extension", assets, id="match extension"),
        pytest.param("prefix*.extension", assets, id="match prefix and extension"),
        pytest.param("*suffix.extension", assets, id="match suffix and extension"),
        pytest.param("prefix*suffix.extension", assets, id="match prefix, suffix, and extension"),
    ]
)
@mock.patch("atacac.differentiate.log")
@mock.patch("atacac.differentiate.load_asset")
@mock.patch("atacac.differentiate.tower_receive")
def test_main(mock_tower_receive, mock_load_asset, mock_log, assets_glob, assets):
    good_files = [assets_glob.replace("*", f"_{value}_") for sublist in assets.values() for value in sublist]
    wrong_files = ["file", ".file", "file.", "file.file"]

    mock_dir = MockDir()
    mock_dir.add_file(good_files)
    mock_dir.add_file(wrong_files)

    os.environ["ASSETS_GLOB"] = os.path.join(mock_dir.path, assets_glob)

    regex = re.compile("^.*_([A-Z])_.*$")

    def custom_load_asset(file_name):
        return {
            "name": f"{file_name}",
            "asset_type": "job_template",
            "extra_vars": (  # this property must be string
                "{}"
            )
        }

    def custom_tower_receive(asset_type, asset_name):
        asset = {
            "name": f"{asset_name}",
            "asset_type": f"{asset_type}",
            "extra_vars": (  # this property must be string
                "{}"
            )
        }

        infix = regex.match(asset_name).group(1)

        if infix in assets["different"]:
            # add a nonexisting property to create an asset difference
            asset["different"] = True
        elif infix in assets["missing"]:
            raise TowerCLIError("exception raised on missing asset")

        return [asset]

    mock_load_asset.side_effect = custom_load_asset
    mock_tower_receive.side_effect = custom_tower_receive

    runner = CliRunner()
    result = runner.invoke(differentiate.main)

    assert result.output == ""
    assert result.exit_code == 0
    assert result.exception is None

    # similar ... 1 INFO
    # different ... 1 INFO + 1 WARN + 2 INFO
    # missing ... 1 INFO ... +1 as FATAL if missing
    assert mock_log.call_count == (
        len(assets["similar"]) + len(assets["different"]) * 4 + len(assets["missing"]) + 1
    )

    assert mock_load_asset.call_count == len(good_files)
    assert mock_tower_receive.call_count == len(good_files)
