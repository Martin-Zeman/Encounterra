import pytest


class SingletonClass:
    _instance = None

    def __new__(cls, number):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.number = number
        return cls._instance


