from time import time
import os
import logging
import sys
from .Database import TeleGroup, TeleMember, TeleAccount
import yaml

dir_path = os.path.dirname(os.path.realpath(__file__))
DATA_LOCATION = './log/'
loggers = {}

def init_logger():
    for file in os.listdir(DATA_LOCATION):
        if file == 'error.log':
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
    
    logger.propagate = False
    loggers[name] = logger
    return logger

logger = get_logger(__name__)

def update_groups(list):
    try:
        logger.debug("Removing old groups")
        TeleGroup.truncate_table()
    except:
        logger.error("Error on deleting groups")
        return
    
    try:
        logger.debug("Inserting new groups to db")
        idx = 0
        data = []
        for i in list:
            data.append ({
                "order" : idx,
                "id" : i.id,
                "title" : i.title if i.title else "-",
                "access_hash": i.access_hash
            })
            idx+=1
        TeleGroup.insert_many(data, fields=[TeleGroup.order, TeleGroup.id, TeleGroup.title, TeleGroup.access_hash]).execute()
    except Exception as e:
        logger.error(f"Error inserting groups to db, {e}")
        
def get_group_details(idx: int) -> TeleGroup:
    try:
        logger.debug(f"Finding group with id : {idx}")
        data = TeleGroup.get(TeleGroup.order == idx)
        logger.debug(f"Found group, name : {data.title}")
        return data
    except:
        logger.error(f"Group dengan id : {idx} tidak dapat ditemukan")
        return None

def set_group_destination(idx: int):
    try:
        logger.info("Removing old destination group (If exists)")
        old_group = TeleGroup.select().where(TeleGroup.is_destination == True)
        for i in old_group:
            i.is_destination = False
            i.save()
        logger.info(f"Setting group destination to id : {idx}")
        group : TeleGroup = TeleGroup.get(
            TeleGroup.order == idx
        )
        group.is_destination = True
        group.save()
        return True
    except:
        logger.error("Error setting group destination")
        return False
       
def get_saved_dest():
    try:
        logger.info("Checking if there's saved destination in database")
        data = TeleGroup.get(
            TeleGroup.is_destination == True
        )
        return data
    except:
        logger.error("Error getting saved destination from database")
        return None

def get_main_tele_account():
    try:
        logger.info("Getting main telegram account")
        with open("./data/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        data = config["ADDER_BOT"]["MAIN_ACCOUNT"]
        data = data.split(';')
        return data
    except:
        logger.error("Error retrieving main telegram account, system exitting now")
        sys.exit()

def get_tele_account() -> TeleAccount:
    try:
        logger.debug("Getting new account from db")
        acc :TeleAccount = TeleAccount.get(
            TeleAccount.is_active == False
        )
        if acc == None:
            raise
        acc.is_active = True
        acc.save()
        return acc
    except:
        logger.error("Unablt to retrieve available account! Either there's no account left or all of the accounts are currently in use.")
        
def release_all_tele_account():
    try:
        logger.info("Releasing all tele account")
        accs = TeleAccount.select()
        for acc in accs:
            acc.is_active = False
            acc.save()
        logger.info("Done releasing all accounts")
    except:
        logger.error("Error releasing all accounts")

def release_tele_account(API_ID : str):
    try:
        logger.info(f"Done with account : {API_ID}")
        acc = TeleAccount.get(
            TeleAccount.API_ID == API_ID
        )
        acc.is_active = False
        acc.save()
    except:
        logger.error(f"Error releasing account {API_ID}")
        
def init_tele_accounts():
    try:
        logger.info("Initializing telegram accounts from config")
        
        with open("./data/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        ACCOUNT_LIST = config["ADDER_BOT"]["ACCOUNTS"]
        for acc in ACCOUNT_LIST:
            data = acc.split(';')
            api_id = data[0]
            api_hash = data[1]
            phone_num = data[2]
            try:
                TeleAccount.get(
                    TeleAccount.API_ID == api_id
                )
            except:
                TeleAccount.create(
                    API_ID = api_id,
                    API_HASH = api_hash,
                    PHONE_NUM = phone_num
                )
    except Exception as e:
        logger.error("Error Initializing telegram accounts")
        print(e)

def init_program():
    init_tele_accounts()