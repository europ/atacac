import functools

from yamale.validators import Validator


@functools.lru_cache(None)
def _load_list_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]


class User(Validator):
    tag = 'user'
    _valid_users = _load_list_from_file('validators/config/user-list.txt')

    def _is_valid(self, value):
        return value in self._valid_users


class Team(Validator):
    tag = 'team'
    _valid_teams = _load_list_from_file('validators/config/team-list.txt')

    def _is_valid(self, value):
        return value in self._valid_teams
