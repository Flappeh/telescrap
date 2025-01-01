import yaml
from .Utils import get_logger
import sys

config = dict()
logger = get_logger(__name__)


logger.info("Initializing environment variables")
try:
    with open("./data/config.yaml", "r") as f:
        config = yaml.safe_load(f)
except:
    logger.error("File config tidak ditemukan!")
    sys.exit()

    

API_ID = config["ADDER_BOT"]["API_ID"] 
API_HASH = config["ADDER_BOT"]["API_HASH"] 
PHONE_NUM = config["ADDER_BOT"]["PHONE_NUM"]

BOT_NAME=config["TELE_BOT"]["BOT_NAME"] 
BOT_TOKEN=config["TELE_BOT"]["BOT_TOKEN"] 
BOT_DISPLAY_NAME=config["TELE_BOT"]["BOT_DISPLAY_NAME"]