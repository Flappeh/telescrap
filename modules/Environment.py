import yaml
from .Utils import get_logger
import sys
import shutil
import os

config = dict()
logger = get_logger(__name__)
API_ID = ""
API_HASH = ""
PHONE_NUM = ""
BOT_NAME = ""
BOT_TOKEN = ""
BOT_DISPLAY_NAME = ""

def init_env():
    logger.info("Initializing environment variables")
    global config,API_ID,API_HASH,PHONE_NUM,BOT_NAME,BOT_TOKEN,BOT_DISPLAY_NAME
    try:
        with open("./data/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        API_ID = config["ADDER_BOT"]["API_ID"] 
        API_HASH = config["ADDER_BOT"]["API_HASH"] 
        PHONE_NUM = config["ADDER_BOT"]["PHONE_NUM"]
        BOT_NAME=config["TELE_BOT"]["BOT_NAME"] 
        BOT_TOKEN=config["TELE_BOT"]["BOT_TOKEN"] 
        BOT_DISPLAY_NAME=config["TELE_BOT"]["BOT_DISPLAY_NAME"]
        # Reset log folder everytime the bot loads

    except:
        logger.error("File config tidak ditemukan!")
        sys.exit()

    
