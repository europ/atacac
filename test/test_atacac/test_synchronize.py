import os
import textwrap
from unittest import mock
from test.utils import MockDir

import pytest  # pylint: disable=import-error
from click.testing import CliRunner

from atacac import synchronize


@pytest.mark.parametrize(
    "assets_glob",
    [
        pytest.param("prefix*", id="with schema validate files matching prefix"),
        pytest.param("*.extension", id="with schema validate files matching extension"),
        pytest.param("prefix*.extension", id="with schema validate files matching prefix and extension"),
        pytest.param("*suffix.extension", id="with schema validate files matching suffix and extension"),
        pytest.param(
            "prefix*suffix.extension",
            id="with schema validate files matching prefix, suffix, and extension"
        ),
    ]
)
@mock.patch("atacac.synchronize.log")
@mock.patch("atacac.synchronize.tower_list")
def test_main(mock_tower_list, mock_log, assets_glob):
    good_files = [assets_glob.replace("*", f"_{infix}_") for infix in ["F", "Z", "A", "M"]]
    wrong_files = ["file", ".file", "file.", "file.file"]

    mock_dir = MockDir()

    mock_dir.add_file(good_files[0], content=textwrap.dedent(
        """\
        ---
        asset_type: job_template
        name: ONE

        """
    ))
    mock_dir.add_file(good_files[1], content=textwrap.dedent(
        """\
        ---
        asset_type: job_template
        name: TWO

        """
    ))
    mock_dir.add_file(good_files[2], content=textwrap.dedent(
        """\
        ---
        asset_type: job_template
        name: THREE

        """
    ))
    mock_dir.add_file(good_files[3], content=textwrap.dedent(
        """\
        ---
        asset_type: job_template
        name: FOUR

        """
    ))

    mock_dir.add_file(wrong_files)

    os.environ["ASSETS_GLOB"] = os.path.join(mock_dir.path, assets_glob)
    os.environ["LABEL_ID"] = "12345"

    mock_tower_list.return_value = [
        {"name": "ONE"},
        {"name": "TWO"},
        {"name": "TEN"},
        {"name": "ELEVEN"}
    ]

    runner = CliRunner()
    result = runner.invoke(synchronize.main)

    assert result.output == ""
    assert result.exit_code == 0
    assert result.exception is None

    assert sorted([call.args[0] for call in mock_log.call_args_list]) == sorted([
        "INFO",  # TWO
        "INFO",  # ONE
        "WARNING",  # FOUR
        "WARNING",  # THREE
        "ERROR",  # TEN
        "ERROR",  # ELEVEN
        "INFO",  # informative note
        "ERROR"  # abort message
    ])

    mock_tower_list.assert_called_once()
