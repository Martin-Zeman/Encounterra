import logging

class LogFormatter(logging.Formatter):
    """Team-colored logging formatter"""

    # grey = '\x1b[38;21m'
    # blue = '\x1b[38;5;39m'
    # yellow = '\x1b[38;5;226m'
    # red = '\x1b[38;5;196m'
    # bold_red = '\x1b[31;1m'
    # white = "\u001b[37m"
    # reset = '\x1b[0m'

    def __init__(self):
        super().__init__()
        self.fmt = '%(team)s %(message)s \x1b[0m'
        self.TEAM_COLORS = {
            "Blue": '\x1b[38;5;39m',
            "Red": '\x1b[38;5;196m'
        }

    def format(self, record):
        formatter = logging.Formatter(self.fmt)
        if not hasattr(record, 'team'):
            record.team = ""
        formatted_msg = formatter.format(record)
        msg_parts = formatted_msg.split()
        try:
            team_color = self.TEAM_COLORS[msg_parts[0]]
            return " ".join([team_color, *msg_parts[1:]])
        except KeyError:
            return formatted_msg
