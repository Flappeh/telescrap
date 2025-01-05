import os
import logging
import sys


dir_path = os.path.dirname(os.path.realpath(__file__))
DATA_LOCATION = './log/'
loggers = {}


def init_logger():
    for file in os.listdir(DATA_LOCATION):
        if ".log" in file:
            with open(DATA_LOCATION + file, 'w') as f:
                f.write('')

def get_logger(name=None):
    global loggers
    if not name:
        name = __name__
    if loggers.get(name):
        return loggers.get(name)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Check if handlers are already added
    if not logger.hasHandlers():
        stream_handler = logging.StreamHandler(sys.stdout)
        log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)
        
        # File handler untuk log level = Error
        error_handler = logging.FileHandler(DATA_LOCATION + "error.log", mode='a')  # 'a' for append mode
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)
        
        
        # File handler untuk log level = Debug
        debug_handler = logging.FileHandler(DATA_LOCATION + "debug.log", mode='a')  # 'a' for append mode
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        debug_handler.setFormatter(debug_formatter)
        logger.addHandler(debug_handler)
    
    logger.propagate = False
    loggers[name] = logger
    return logger