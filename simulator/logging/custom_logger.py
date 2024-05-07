import logging
import sys
from enum import Enum, auto

from ..logging.log_formatter import LogFormatter


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


class CustomLogger:

    def __init__(self, level, stream=True, file_path=None):
        logging.root.handlers = []  # remove the root logger
        logger = logging.getLogger("Encounterra")
        logger.setLevel(level)
        logger.propagate = False  # Prevent log messages from propagating to ancestor loggers

        if stream:
            stdout_handler = logging.StreamHandler(stream=sys.stdout)
            stdout_handler.setFormatter(LogFormatter())
            stdout_handler.setLevel(level)
            logger.addHandler(stdout_handler)

        if file_path:
            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
