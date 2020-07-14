import os
import tempfile
import textwrap
from unittest import mock
from test.utils import MockDir

import pytest
from click.testing import CliRunner

from atacac import validate


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
@mock.patch("atacac.validate.log")
def test_validate(mock_log, assets_glob):
    good_files = [assets_glob.replace("*", f"_{infix}_") for infix in ["F", "Z", "A", "M"]]
    wrong_files = ["file", ".file", "file.", "file.file"]

    content = textwrap.dedent(
        """\
        ---
        a:
          b: bbb
          c: true
          d:
            - 1
            - 2
            - 3

        """
    )

    schema = textwrap.dedent(
        """\
        ---
        a:
          b: str()
          c: bool()
          d: list(int())

        """
    )

    mock_dir = MockDir()
    mock_dir.add_file(good_files, content=content)
    mock_dir.add_file(wrong_files, content=content)

    os.environ["ASSETS_GLOB"] = os.path.join(mock_dir.path, assets_glob)

    with tempfile.NamedTemporaryFile() as file_schema:
        file_schema.write(bytes(schema, encoding="utf-8"))
        file_schema.seek(0)

        os.environ["ASSETS_SCHEMA"] = file_schema.name

        runner = CliRunner()
        result = runner.invoke(validate.main)

        assert result.output == ""
        assert result.exit_code == 0
        assert result.exception is None

        assert mock_log.call_count == len(good_files) + 1
