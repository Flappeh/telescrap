from time import time
import os
import logging
import sys
import shutil


dir_path = os.path.dirname(os.path.realpath(__file__))
DATA_LOCATION = './log/'
loggers = {}

# Reset log folder everytime the bot loads
shutil.rmtree('./log')
os.mkdir('./log')



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
    
    logger.propagate = False
    loggers[name] = logger
    return logger

logger = get_logger(__name__)