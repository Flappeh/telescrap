import yaml
from modules.utils.common import get_logger
import sys
import shutil
import os

config = dict()
logger = get_logger(__name__)

with open("./data/config.yaml", "r") as f:
    config = yaml.safe_load(f)

API_HASH = config["ADDER_BOT"]["API_HASH"]
API_ID = config["ADDER_BOT"]["API_ID"]
BOT_NAME=config["TELE_BOT"]["BOT_NAME"] 
BOT_TOKEN=config["TELE_BOT"]["BOT_TOKEN"] 
BOT_DISPLAY_NAME=config["TELE_BOT"]["BOT_DISPLAY_NAME"]