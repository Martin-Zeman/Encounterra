from enum import Enum
import copy


class Teams:

    class Color(Enum):
        BLUE = 1
        RED = 2

        def __str__(self):
            match self:
                case self.BLUE:
                    return "\x1b[38;5;39m"
                case self.RED:
                    return "\x1b[38;5;196m"
                case _:
                    return ""

    def __init__(self):
        self.team_book = {}  # maps team_color -> [list of combatants]
        self.reverse_team_book = {}  # maps combatant -> team_color
        self.id_to_combatant = {-1: None}  # maps combatant id -> combatant
        self.team_color_codes = {}

    def add_combatant_to_team(self, combatant, team_color):
        try:
            self.id_to_combatant[combatant.id] = combatant
            self.reverse_team_book[combatant] = team_color
            self.team_book[team_color].append(combatant)
        except KeyError:
            self.team_book[team_color] = [combatant]
        combatant.add_team(team_color)

    def replace_combatant(self, combatant_old, combatant_new):
        """
        Helper function for wildshape
        """
        self.reverse_team_book[combatant_new] = self.reverse_team_book[combatant_old]
        del self.reverse_team_book[combatant_old]
        self.team_book[self.reverse_team_book[combatant_new]].remove(combatant_old)
        self.team_book[self.reverse_team_book[combatant_new]].append(combatant_new)
        del self.id_to_combatant[combatant_old.id]
        self.id_to_combatant[combatant_new.id] = combatant_new

    def get_team_color_code(self, combatant):
        return str(self.reverse_team_book[combatant])

    def get_team_color(self, combatant):
        return self.reverse_team_book[combatant]

    def get_surviving_teams(self):
        return [name for name, combatants in self.team_book.items() if any(ch.is_alive() for ch in combatants)]

    def get_death_count(self):
        return tuple(len(self.team_book[color]) - sum(ch.is_alive() for ch in self.team_book[color]) for color in
                 [self.Color.BLUE, self.Color.RED])

    def get_team_colors(self):
        return self.team_book.keys()

    def are_allies(self, first, second):
        return True if self.reverse_team_book[first] == self.reverse_team_book[second] else False

    def are_enemies(self, first, second):
        return False if self.reverse_team_book[first] == self.reverse_team_book[second] else True

    def get_team(self, combatant):
        return self.reverse_team_book[combatant]

    def get_allies(self, combatant):
        team_members = copy.copy(self.team_book[self.reverse_team_book[combatant]])
        team_members.remove(combatant)  # Remove self
        return team_members

    def get_enemies(self, combatant):
        self_team = self.reverse_team_book[combatant]
        other_team = self.Color.RED if self_team is self.Color.BLUE else self.Color.BLUE
        try:
            return self.team_book[other_team]
        except KeyError:
            # This can only happen in test scenarios
            return []
