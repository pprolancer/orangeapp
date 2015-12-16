import logging
import os
from orange.conf import config
from logging.handlers import RotatingFileHandler

loggers = {}


def get_logger(name, filename=None, filedir=None, handler=None,
               formatter=None, level=None):
    filename = filename or '%s.log' % name
    filedir = filedir or config.get('general', 'LOG_DIR')
    log_path = os.path.join(filedir, filename)
    handler = handler or RotatingFileHandler(filename=log_path,
                                             maxBytes=100 * 1024000,
                                             backupCount=10)
    formatter = formatter or logging.Formatter(config.get('general',
                                               'LOG_FORMAT'))
    level = level or config.get('general', 'LOG_ROOT_LEVEL')

    handler = {
        'handler': handler,
        'formatter': formatter,
        'level': level
    }

    logger = loggers.get(name)
    if logger is None:
        logger = logging.getLogger(name)
        logger.setLevel(config.get('general', 'LOG_ROOT_LEVEL'))

        h = handler['handler']
        h.setFormatter(handler['formatter'])
        h.setLevel(handler['level'])
        logger.addHandler(h)
        loggers[name] = logger

    return logger
