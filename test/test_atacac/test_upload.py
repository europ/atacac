import os
import tempfile
from unittest import mock

import pytest
from click.testing import CliRunner

from atacac import upload


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
@mock.patch("atacac.upload.tower_send")
def test_main(mock_tower_send, assets_glob):
    good_files = [assets_glob.replace("*", f"_{infix}_") for infix in ["F", "Z", "A", "M"]]
    wrong_files = ["file", ".file", "file.", "file.file"]

    with tempfile.TemporaryDirectory() as tmp_dir:
        for file in [*good_files, *wrong_files]:
            with open(os.path.join(tmp_dir, file), "w") as f:
                f.write("---\n")

        os.environ["ASSETS_GLOB"] = os.path.join(tmp_dir, assets_glob)

        runner = CliRunner()
        result = runner.invoke(upload.main)

        assert result.output == ""
        assert result.exit_code == 0
        assert result.exception is None

        mock_tower_send.assert_called_once()
        mock_tower_send.assert_called_with(sorted([os.path.join(tmp_dir, file) for file in good_files]))
