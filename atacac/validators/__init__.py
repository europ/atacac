import inspect

from yamale.validators import DefaultValidators, Validator

from atacac._utils import log
from atacac.validators import builtin


def _is_validator(cls):
    return inspect.isclass(cls) and issubclass(cls, Validator) and cls is not Validator


def load(files=None):
    validators = DefaultValidators.copy()

    # Load builtin validators.
    for name in dir(builtin):
        obj = getattr(builtin, name)
        if _is_validator(obj):
            validators[obj.tag] = obj

    # Load custom validators from external files.
    for f_path in files or []:
        log('INFO', f'Loading validators from user script {f_path!r}')
        with open(f_path, 'rb') as f:
            code = compile(f.read(), f_path, 'exec')

        globals_ = {}
        locals_ = {}
        exec(code, globals_, locals_)

        for obj in locals_.values():
            if _is_validator(obj):
                validators[obj.tag] = obj

    return validators
