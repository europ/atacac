from yamale.validators import Validator


class Example(Validator):
    tag = 'example'

    def _is_valid(self, value):
        return value == 'example'


class Dict(Validator):
    tag = 'dict'

    def _is_valid(self, value):
        return isinstance(value, dict)
