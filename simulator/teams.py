from enum import Enum


class Teams:

    class Color(Enum):
        BLUE = 1
        RED = 2

    COLOR_CODES = {
        Color.BLUE: "\x1b[38;5;39m",
        Color.RED: "\x1b[38;5;196m"
    }

    def __init__(self):
        self.team_book = {}  # maps team_color -> [list of combatants]
        self.reverse_team_book = {}  # maps combatant -> team_color
        self.team_color_codes = {}

    def add_combatant_to_team(self, combatant, team_color):
        try:
            self.reverse_team_book[combatant] = team_color
            self.team_book[team_color].append(combatant)
        except KeyError:
            self.team_book[team_color] = [combatant]
        combatant.add_team(team_color)

    def get_team_color_code(self, combatant):
        return self.COLOR_CODES[self.reverse_team_book[combatant]]
    # def get_survivors_of_team(self, team_name):
    #     return [ch.get_name() for ch in self.team_book[team_name] if ch.is_alive()]
    #
    # def get_survivors_per_teams(self):
    #     return {k: [ch for ch in combatants if ch.is_alive()] for (k, combatants) in self.team_book.values()}

    def get_surviving_teams(self):
        surviving_teams = []
        for name, combatants in self.team_book.items():
            if any([ch.get_name() for ch in combatants if ch.is_alive()]):
                surviving_teams.append(name)
        return surviving_teams

    def get_team_colors(self):
        return self.team_book.keys()

    def are_allies(self, first, second):
        return True if self.reverse_team_book[first] == self.reverse_team_book[second] else False

    def are_enemies(self, first, second):
        return False if self.reverse_team_book[first] == self.reverse_team_book[second] else True

    def get_team(self, combatant):
        return self.reverse_team_book[combatant]
