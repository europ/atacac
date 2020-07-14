import os
import sys
import textwrap
from test.utils import MockDir

import pytest
from yamale.validators import DefaultValidators, Validator

from atacac import validators


class simple_class:
    pass


class sub_Validator(Validator):
    pass


class sub_sub_Validator(sub_Validator):
    pass


class sub_sub_sub_Validator(sub_sub_Validator):
    pass


@pytest.mark.parametrize(
    "cls, result",
    [
        pytest.param(
            sub_Validator,
            True,
            id="correct value (subclass of Validator)"
        ),
        pytest.param(
            sub_sub_Validator,
            True,
            id="correct value (subclass of subclass of Validator)"
        ),
        pytest.param(
            sub_sub_sub_Validator,
            True,
            id="correct value (subclass of subclass of subclass of Validator)"
        ),
        pytest.param(Validator, False, id="incorrect value (Validator)"),
        pytest.param(simple_class, False, id="incorrect value (simple class)"),
        pytest.param(str, False, id="incorrect value (string)"),
        pytest.param(list, False, id="incorrect value (list)"),
        pytest.param(tuple, False, id="incorrect value (tuple)"),
        pytest.param(dict, False, id="incorrect value (dict)"),
    ]
)
def test__is_validator(cls, result):
    assert validators._is_validator(cls) == result


def test_load():
    mock_dir = MockDir()
    mock_dir.add_file("tmp_custom_validators.py", textwrap.dedent(
        """\
        from yamale.validators import Validator

        class custom_validator_1(Validator):
            tag = 'custom_validator_1'

            def _is_valid(self, value):
                return value == 'custom_validator_1'


        class custom_validator_2(Validator):
            tag = 'custom_validator_2'

            def _is_valid(self, value):
                return value == 'custom_validator_2'

        """
    ))

    result = validators.load([os.path.join(mock_dir.path, "tmp_custom_validators.py")])

    sys.path.append(mock_dir.path)
    from tmp_custom_validators import custom_validator_1, custom_validator_2  # pylint: disable=import-error

    expected = {
        **DefaultValidators,
        "example": validators.builtin.Example,
        "dict": validators.builtin.Dict,
        "custom_validator_1": custom_validator_1,
        "custom_validator_2": custom_validator_2
    }

    assert sorted(result.keys()) == sorted(expected.keys())
    assert sorted(item.__name__ for item in result.values()) == sorted(
        item.__name__ for item in expected.values())
