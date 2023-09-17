import logging

class LogFormatter(logging.Formatter):
    """Team-colored logging formatter"""

    def __init__(self):
        super().__init__()
        self.fmt = '%(team)s%(message)s\x1b[0m'

    def format(self, record):
        formatter = logging.Formatter(self.fmt)
        if not hasattr(record, 'team'):
            record.team = ""
        formatted_msg = formatter.format(record)
        return formatted_msg
