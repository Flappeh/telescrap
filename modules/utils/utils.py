from time import time
import sys
from telethon.tl.functions.messages import GetDialogsRequest
from multiprocessing import set_start_method
from modules.database import TeleGroup, TeleMember, TeleAccount
import yaml
import telethon.errors as tele_error
from typing import List
import multiprocessing as mp
from telethon.tl.types import InputPeerEmpty
from telethon.sync import TelegramClient
from modules.utils.common import get_logger
from modules.utils.adder import AdderBot
from modules.environment import API_ID, API_HASH
import os

logger = get_logger(__name__)
    
def split_list(data, n):
    k, m = divmod(len(data), n)
    return (data[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def insert_members(members):
    try:
        logger.debug("Removing old members from db")
        TeleMember.truncate_table()
    except:
        logger.error("Error removing old data from members table")
        return
    
    try:
        logger.debug("Inserting member data to database")
        TeleMember.insert_many(members, fields=[TeleMember.username, TeleMember.user_id, TeleMember.access_hash, TeleMember.group, TeleMember.group_id]).execute()
    except Exception as e:
        logger.error(f"Error inserting member data to database, message : {e}")

def get_all_members(n):
    try:
        logger.info("Getting all member data")
        members = [member for member in TeleMember.select()]
        return list(split_list(members, n))
    except:
        logger.error("Error getting member data")
      
def get_active_accounts():
    try:
        accounts = [ acc for acc in TeleAccount.select().where(TeleAccount.logged_in == True)]
        return accounts
    except:
        logger.error("Error getting active accounts")
      
async def get_group_by_title(scraper: TelegramClient, group_title):
        chats = []
        last_date = None
        chunk_size = 200
        
        result = await scraper(GetDialogsRequest(
                    offset_date=last_date,
                    offset_id=0,
                    offset_peer=InputPeerEmpty(),
                    limit=chunk_size,
                    hash = 0
                ))
        chats.extend(result.chats)

        for chat in chats:
            try:
                if chat.megagroup == True and chat.title == group_title:
                    return chat
            except:
                continue
        return None

def update_groups(list):
    logger.debug("Getting old destination")
    dest = get_saved_dest()
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
        old_title = dest.title if dest else ""
        for i in list:
            new_group = {
                "order" : idx,
                "id" : i.id,
                "title" : i.title if i.title else "-",
                "access_hash": i.access_hash
            }
            if i.title == old_title:
                new_group["is_destination"] = True
            else:
                new_group["is_destination"] = False
            data.append (new_group)
            idx+=1
        TeleGroup.insert_many(data, fields=[TeleGroup.order, TeleGroup.id, TeleGroup.title, TeleGroup.access_hash, TeleGroup.is_destination]).execute()
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

def set_group_destination(group):
    try:
        logger.info("Removing old destination group (If exists)")
        old_group = TeleGroup.select().where(TeleGroup.is_destination == True)
        for i in old_group:
            i.is_destination = False
            i.save()
        logger.info(f"Setting group destination to url : {group["url"]}")
        try:
            found_group : TeleGroup = TeleGroup.get(
                TeleGroup.url == group["url"]
            )
            found_group.is_destination = True
            found_group.private = group["private"]
            found_group.title = group["title"]
            found_group.save()
        except:
            TeleGroup.create(
                is_destination = True,
                url = group["url"],
                private = group["private"],
                title = group["title"]
            )
        return True
    except Exception as e:
        logger.error(f"Error setting group destination, {e}")
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
        return data
    except:
        logger.error("Error retrieving main telegram account, system exitting now")
        sys.exit()

def get_tele_account() -> TeleAccount:
    try:
        logger.debug("Getting new account from db")
        acc :TeleAccount = TeleAccount.get(
            TeleAccount.is_active == False,
            TeleAccount.logged_in == True
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

def release_tele_account(PHONE_NUM : str):
    try:
        logger.info(f"Done with account : {PHONE_NUM}")
        acc = TeleAccount.get(
            TeleAccount.PHONE_NUM == PHONE_NUM
        )
        acc.is_active = False
        acc.save()
    except:
        logger.error(f"Error releasing account {PHONE_NUM}")
        
def add_accounts_to_db():
    try:
        logger.info("Importing telegram accounts from config")
        
        main_acc = get_main_tele_account()
        
        with open("./data/config.yaml", "r") as f:
            config = yaml.safe_load(f)
            
        ACCOUNT_LIST : List[str]= config["ADDER_BOT"]["ACCOUNTS"]
        ACCOUNT_LIST.append(main_acc)
        
        for acc in ACCOUNT_LIST:
            try:
                TeleAccount.get(
                    TeleAccount.PHONE_NUM == acc
                )
            except:
                new_acc = TeleAccount.create(
                    PHONE_NUM = acc
                )
                if acc == main_acc:
                    new_acc.is_main = True
                    new_acc.save()
        logger.info("Finished importing telegram accounts from config")
        
    except Exception as e:
        logger.error(f"Error Initializing telegram accounts {e}")

def confirm_telegram_login():
    confirm = input("Apakah ingin login untuk akun ini (y/n) : ")
    if confirm.lower() != 'y' and confirm.lower() != 'n':
        print("Mohon konfirmasi dengan mengirimkan 'y' atau 'n'")
        confirm_telegram_login()
    if confirm.lower() == 'y' or confirm.lower() == '':
        return True
    return False

def telegram_initialize_login(account: TeleAccount, tries: int = 0):
    try:
        phone = account.PHONE_NUM
        if tries == 3:
            raise ValueError("Percobaan login melebihi batas maximum. Nomor akan dilewati")
        logger.info(f"Mulai login untuk nomor : {phone}")
        if confirm_telegram_login():
            client = TelegramClient(f"data/sessions/{phone}", API_ID, API_HASH)
            client.connect()
            client.start(phone)
            client.disconnect()
            del client
            return True
        else:
            logger.info(f"Skipping phone number: {account.PHONE_NUM}")
            return False
    except tele_error.PhoneNumberBannedError:
        logger.error(f"Number : {account.PHONE_NUM} is banned")
        return False
    except tele_error.SessionPasswordNeededError:
        try:
            password = input("Butuh password untuk login. Password : ")
            client.sign_in(password=password)
        except Exception as e:
            print(f"Error : {e.__class__.__name__}, message : {e}")    
    except tele_error.PhoneCodeInvalidError as e:
        tries += 1
        logger.error(f"Kode yang di enter invalid, mohon coba kembali.")
        telegram_initialize_login(account, tries)
    
    except tele_error.FloodWaitError as e:
        logger.error(f"Terdapat error flood untuk nomor ini. Details {e} ")
        
    except Exception as e:
        logger.error(f"Error encountered when logging in account. Type: {e.__class__.__name__}, Message: {e}")
        return False
    
def get_all_db_accounts() -> List[TeleAccount]:
    try:
        logger.debug("Getting all stored accounts data")
        data = [account for account in TeleAccount.select()]
        return data
    except:
        logger.error("Error getting accounts from database, exiting now...")
        sys.exit()
    
def get_all_active_accounts() -> List[TeleAccount]:
    try:
        logger.debug("Getting all active accounts data")
        data = [account for account in TeleAccount.select().where(TeleAccount.logged_in == True)]
        return data
    except:
        logger.error("Error getting accounts from database, exiting now...")
        sys.exit()

    
def login_tele_accounts():
    try:
        logger.info("Logging into telegram accounts")
        accounts = get_all_db_accounts()
        verif_count = 0
        for acc in accounts:
            done = telegram_initialize_login(acc)
            if done:
                acc.logged_in = True
                acc.save()
                verif_count += 1
            else:
                acc.delete()
        logger.info(f"Setup account selesai, jumlah akun yang telah login : {verif_count}")
    except Exception as e:
        logger.error(f"Error encountered when logging into telegram accounts, exiting now. message {e}")
        sys.exit()

def sub_scrape_process(data):
    member_ids = [member["user_id"] for member in data['members']]
    bot = AdderBot(data['acc'],data['src'],data['dest'],member_ids)
    bot.run()

def start_scrape_process(grp_dest:TeleGroup, group_src: str, members):
    try:
        logger.info("Mulai proses pengambilan data")
        accounts = get_all_active_accounts()
        members_split = list(split_list(members, len(accounts)))
        
        proc_list = []
        
        for idx,acc in enumerate(accounts):
            process = mp.Process(target=sub_scrape_process, args=({
            "dest": {
                "url": grp_dest.url,
                "title": grp_dest.title,
                "private": grp_dest.private,
                },
            "src": group_src,
            "members": members_split[idx],
            "acc": acc
            },))
            proc_list.append(process)
            process.start()
            
        for i in proc_list:
            i.join()
    except Exception as e:
        logger.error(f"Error occured on scraping process. Details : {e}")
        
def init_program():
    set_start_method('spawn', force=True)
    mp.freeze_support()
    add_accounts_to_db()
    login_tele_accounts()