class Teams:
    def __init__(self):
        self.__team_book = {}
        self.__reverse_team_book = {}
        # self.__name = name
        # self.__characters = characters

    def add_char_to_team(self, character, team_name):
        try:
            self.__reverse_team_book[character] = team_name
            self.__team_book[team_name].append(character)
        except KeyError:
            self.__team_book[team_name] = [character]

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
