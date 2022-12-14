class Teams:

    BLUE = 1
    RED = 2

    COLOR_CODES = {
        BLUE: "\x1b[38;5;39m",
        RED: "\x1b[38;5;196m"
    }

    def __init__(self):
        self.__team_book = {} # maps team_name -> [list of characters]
        self.__reverse_team_book = {} # maps character -> team_name
        self.team_color_codes = {}
        # self.__name = name
        # self.__characters = characters

    def add_char_to_team(self, character, team_name):
        try:
            self.__reverse_team_book[character] = team_name
            self.__team_book[team_name].append(character)
        except KeyError:
            self.__team_book[team_name] = [character]
        character.add_team(team_name)

    def set_team_color(self, team_name, color):
        if color == self.BLUE or color == self.RED:
            self.team_color_codes[team_name] = self.COLOR_CODES[color]


    def get_team_color_code(self, character):
        return self.team_color_codes[self.__reverse_team_book[character]]
    # def get_survivors_of_team(self, team_name):
    #     return [ch.get_name() for ch in self.__team_book[team_name] if ch.is_alive()]
    #
    # def get_survivors_per_teams(self):
    #     return {k: [ch for ch in characters if ch.is_alive()] for (k, characters) in self.__team_book.values()}

    def get_surviving_teams(self):
        surviving_teams = []
        for name, characters in self.__team_book.items():
            if any([ch.get_name() for ch in characters if ch.is_alive()]):
                surviving_teams.append(name)
        return surviving_teams


    def get_team_names(self):
        return self.__team_book.keys()

    def are_allies(self, first, second):
        return True if self.__reverse_team_book[first] == self.__reverse_team_book[second] else False

    def get_team(self, character):
        return self.__reverse_team_book[character]
