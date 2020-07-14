import os
import re
import textwrap
from test.utils import MockDir

import pytest
import yamale
from yamale.validators import DefaultValidators

from atacac.validators.builtin import Example, Dict


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("example", id="correct value"),
        pytest.param("xample", id="incorrect value (1)"),
        pytest.param("exampl", id="incorrect value (2)"),
        pytest.param("examplee", id="incorrect value (3)"),
        pytest.param("eexample", id="incorrect value (4)"),
        pytest.param("exammple", id="incorrect value (5)"),
        pytest.param("abcdefgh", id="incorrect value (6)"),
    ]
)
def test_Example__is_valid(value):
    validators = {
        **DefaultValidators,
        Example.tag: Example
    }

    mock_dir = MockDir()

    mock_dir.add_file("schema", textwrap.dedent(
        """\
        ---
        key: example()
        """
    ))

    mock_dir.add_file("data", textwrap.dedent(
        f"""\
        ---
        key: {value}
        """
    ))

    schema = yamale.make_schema(os.path.join(mock_dir.path, "schema"), validators=validators)
    data = yamale.make_data(os.path.join(mock_dir.path, "data"))

    try:
        result = yamale.validate(schema, data)

        assert value == "example"
        assert result[0].isValid() is True
        assert result[0].errors == []

    except yamale.yamale_error.YamaleError as e:

        assert value != "example"
        assert e.results[0].isValid() is False
        assert f"'{value}' is not a example" in str(e)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("{}", id="correct value (empty dictionary)"),
        pytest.param("{a: 1, b: 2}", id="correct value (nonempty dictionary)"),
        pytest.param("[]", id="incorrect value (empty list)"),
        pytest.param("[1, 2]", id="incorrect value (nonempty list)"),
        pytest.param("1", id="incorrect value (integer)"),
        pytest.param("atacac", id="incorrect value (string)"),
    ]
)
def test_Dict__is_valid(value):
    validators = {
        **DefaultValidators,
        Dict.tag: Dict
    }

    mock_dir = MockDir()

    mock_dir.add_file("schema", textwrap.dedent(
        """\
        ---
        key: dict()
        """
    ))

    mock_dir.add_file("data", textwrap.dedent(
        f"""\
        ---
        key: {value}
        """
    ))

    schema = yamale.make_schema(os.path.join(mock_dir.path, "schema"), validators=validators)
    data = yamale.make_data(os.path.join(mock_dir.path, "data"))

    try:
        result = yamale.validate(schema, data)

        assert re.match("^{.*}$", value)
        assert result[0].isValid() is True
        assert result[0].errors == []

    except yamale.yamale_error.YamaleError as e:

        assert not re.match("^{.*}$", value)
        assert e.results[0].isValid() is False
        assert f"'{value}' is not a dict" in str(e)
