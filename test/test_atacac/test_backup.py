import os
import shutil
import textwrap
from unittest import mock
from test.utils import MockDir

import yaml
import pytest  # pylint: disable=import-error
from click.testing import CliRunner

from atacac import backup


class TestDumper:

    def test_increase_indent(self):
        data = {
            "a": {
                "b1": [1, 2, 3],
                "b2": {
                    "b2_c1": True,
                    "b2_c2": "string-value"
                },
                "b3": "string-value",
                "b4": 123,
                "b5": {
                    "b5_c1": False,
                    "b5_c2": "string-value",
                    "b5_c3": [
                        {"b5c3_x": 1, "b5c3_y": 2, "b5c3_z": 3},
                        {"b5c3_x": 4, "b5c3_y": 5, "b5c3_z": 6},
                        {"b5c3_x": 7, "b5c3_y": 8, "b5c3_z": 7}
                    ],
                    "b5_c4": ["x", "y", "z"]
                }
            }
        }

        result = yaml.dump(data, Dumper=backup.Dumper, default_flow_style=False)

        assert result == textwrap.dedent(
            """\
            a:
              b1:
                - 1
                - 2
                - 3
              b2:
                b2_c1: true
                b2_c2: string-value
              b3: string-value
              b4: 123
              b5:
                b5_c1: false
                b5_c2: string-value
                b5_c3:
                  - b5c3_x: 1
                    b5c3_y: 2
                    b5c3_z: 3
                  - b5c3_x: 4
                    b5c3_y: 5
                    b5c3_z: 6
                  - b5c3_x: 7
                    b5c3_y: 8
                    b5c3_z: 7
                b5_c4:
                  - x
                  - y
                  - z
            """
        )


@pytest.mark.parametrize(
    "assets_glob",
    [
        pytest.param("prefix*", id="match prefix"),
        pytest.param("*.extension", id="match extension"),
        pytest.param("prefix*.extension", id="match prefix and extension"),
        pytest.param("*suffix.extension", id="match suffix and extension"),
        pytest.param("prefix*suffix.extension", id="match prefix, suffix, and extension"),
    ]
)
@mock.patch("atacac.backup.log")
@mock.patch("atacac.backup.load_asset")
@mock.patch("atacac.backup.tower_receive")
def test_main(mock_tower_receive, mock_load_asset, mock_log, assets_glob):
    backup_path = "./backup"

    try:
        shutil.rmtree(backup_path)
    except FileNotFoundError:
        pass

    good_files = [assets_glob.replace("*", f"_{infix}_") for infix in ["F", "Z", "A", "M"]]
    wrong_files = ["file", ".file", "file.", "file.file"]

    mock_dir = MockDir()
    mock_dir.add_file(good_files)
    mock_dir.add_file(wrong_files)

    os.environ["BACKUP_PATH"] = backup_path
    os.environ["ASSETS_GLOB"] = os.path.join(mock_dir.path, assets_glob)

    mock_load_asset.side_effect = lambda file_name: {
        "name": f"LOADASSET {file_name}",
        "asset_type": "job_template",
        "note": "return value of load_asset"
    }
    mock_tower_receive.side_effect = lambda asset_type, asset_name: [{
        "name": f"TOWERRECEIVE {asset_name}",
        "note": "return value of tower_receive"
    }]

    runner = CliRunner()
    result = runner.invoke(backup.main)

    assert result.output == ""
    assert result.exit_code == 0
    assert result.exception is None

    assert mock_log.call_count == len(good_files) * 3
    assert mock_load_asset.call_count == len(good_files)
    assert mock_tower_receive.call_count == len(good_files)

    assert len(os.listdir(backup_path)) == len(good_files)

    file_name_path = mock_dir.path.replace("/", "-").replace(" ", "_")
    assert sorted(os.listdir(backup_path)) == [
        f"TOWERRECEIVE_LOADASSET_{file_name_path}-{file_name}.yml"
        for file_name in sorted(good_files)
    ]

    shutil.rmtree(backup_path)
