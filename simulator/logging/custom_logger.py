import logging
import sys
from enum import Enum, auto

from simulator.logging.log_formatter import LogFormatter


def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Adds a new logging level to the `logging` module and the
    currently configured logging class.
    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
        raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError('{} already defined in logger class'.format(methodName))

    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)

class LogLevel(Enum):
    VERBOSE = auto()
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()

class CustomLogger:

    # VERBOSE_VALUE = logging.DEBUG - 5

    LEVEL_MAPPING = {
        # LogLevel.VERBOSE: VERBOSE_VALUE,
        LogLevel.DEBUG: logging.DEBUG,
        LogLevel.INFO: logging.INFO,
        LogLevel.WARNING: logging.WARNING,
        LogLevel.ERROR: logging.ERROR,
    }

    def __init__(self, level):
        # addLoggingLevel('VERBOSE', self.VERBOSE_VALUE)
        logger = logging.getLogger("EncounTroll")
        logger.setLevel(self.LEVEL_MAPPING[level])
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setFormatter(LogFormatter())
        stdout_handler.setLevel(self.LEVEL_MAPPING[level])
        # stdout_handler.flush = sys.stdout.flush  # Add this line
        logger.addHandler(stdout_handler)
