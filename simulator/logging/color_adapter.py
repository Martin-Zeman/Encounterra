import logging

class ColorAdapter(logging.LoggerAdapter):

    TEAM_COLORS = {"Blue" : '\x1b[38;5;39m', "Red": '\x1b[38;5;196m'}
    RESET = '\x1b[0m'

    def process(self, msg, kwargs):
        return self.TEAM_COLORS[self.extra["team"]] + f'{msg}' + RESET, kwargs