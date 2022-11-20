import logging

class ColorLogger(logging.Logger):

    def info(self, msg, *args, **kwargs):
        return super(ColorLogger, self).info(msg + 'Foo', *args, **kwargs)
