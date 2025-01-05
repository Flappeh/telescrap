from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest, GetMessagesRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser, Channel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
import pytz
from modules.database import TeleGroup, TeleMember
import random
from modules.utils.common import get_logger
from modules.utils import utils
import asyncio
from modules.environment import API_HASH, API_ID
from time import sleep
from datetime import datetime, timedelta

logger = get_logger(__name__)

utc = pytz.UTC

class ScraperAuth():
    def __init__(self):
        self.status = ""
        self.code_hash = ""
        self.auth_code = ""
        
    def to_dict(self):
        return {
         'status': self.status,
         'code_hash': self.code_hash,
         'auth_code': self.auth_code   
        }

class ScraperBot():
    def __init__(self):
        self.API_ID = API_ID
        self.API_HASH = API_HASH
        self.PHONE_NUM = ""
        self.is_child = False
        self.client : TelegramClient = None
        self.sent_code = False
        self.auth_data : ScraperAuth = ScraperAuth()
        self.init_account()
        
    def __del__(self):
        utils.release_tele_account(self.PHONE_NUM)
        
    def init_account(self):
        if self.is_child == False:
            data = utils.get_main_tele_account()
            self.PHONE_NUM = data
        else:
            account = utils.get_tele_account()
            self.PHONE_NUM = account.PHONE_NUM
    
    async def login_client(self, data: ScraperAuth):
        try:
            logger.debug(f"Got data: {data.to_dict()}")
            await self.client.sign_in(
                phone=self.PHONE_NUM, 
                code=data.auth_code,
                phone_code_hash=data.code_hash)
        except Exception as e:
            logger.error(f"Error logging in to client, {e}")
            return False
    
    async def create_client(self):
        self.client = TelegramClient(f"data/sessions/{self.PHONE_NUM}", self.API_ID, self.API_HASH)
        await self.client.connect()
        if not await self.client.is_user_authorized():
            logger.debug("Client not logged in yet")
            if self.sent_code == False:
                code_req = await self.client.send_code_request(self.PHONE_NUM)
                self.auth_data.code_hash = code_req.phone_code_hash
                self.sent_code = True
                self.auth_data.status = "sent_code"
                return self.auth_data
        self.auth_data.status = "done"
        return self.auth_data
    
    async def get_group_details(self, idx) -> TeleGroup:
        data = utils.get_group_details(idx)
        return data
    
    async def get_groups_data(self):
        chats = []
        last_date = None
        chunk_size = 200
        groups=[]
        
        result = await self.client(GetDialogsRequest(
                    offset_date=last_date,
                    offset_id=0,
                    offset_peer=InputPeerEmpty(),
                    limit=chunk_size,
                    hash = 0
                ))
        chats.extend(result.chats)

        for chat in chats:
            try:
                if chat.megagroup == True:
                    groups.append(chat)
            except:
                continue
        return groups
    
    async def check_saved_dest(self):
        data = utils.get_saved_dest()
        return data
    
    async def get_groups_list(self):
        groups = await self.get_groups_data()
        await self.update_db_groups(groups)
        i=0
        response = ""
        for g in groups:
            response += (str(i) + '- ' + g.title + '\n')
            i+=1
        return response
 
    async def update_db_groups(self, groups):
        utils.update_groups(groups)
    
    
    async def fetch_and_store_members(self, group):
        members = []
        logger.info("Proses ambil data user dari group")
        data = await self.client.get_participants(group,aggressive=False)
        for i in data:
            try:
                member = {
                    "username" : i.username if i.username else "",
                    "user_id" : i.id,
                    "access_hash" : i.access_hash,
                    "group" : group.title,
                    "group_id" : group.id
                }
                members.append(member)
            except:
                continue
        return members     
    
                
    
class SubScraperBot(ScraperBot):
    def __init__(self):
        super().__init__()
        self.is_child = True
    
async def get_scraper():
    bot = ScraperBot()
    auth = await bot.create_client()
    return bot, auth

# client = TelegramClient(PHONE_NUM, API_ID, API_HASH)

# client.connect()
# if not client.is_user_authorized():
#     client.send_code_request(PHONE_NUM)
#     client.sign_in(PHONE_NUM, input('Enter the code: '))




# def get(chat_num):
#     #print(chat_num)
#     chats = []
#     last_date = None
#     chunk_size = 200
#     groups=[]
     
#     result = client(GetDialogsRequest(
#                  offset_date=last_date,
#                  offset_id=0,
#                  offset_peer=InputPeerEmpty(),
#                  limit=chunk_size,
#                  hash = 0
#              ))
#     chats.extend(result.chats)

#     for chat in chats:
#         try:
#             if chat.megagroup== True:
#                 groups.append(chat)
#         except:
#             continue

#     g_index = chat_num
#     target_group=groups[int(g_index)]
#     filename = target_group.title 
#     print('Fetching Members from {} ...'.format(filename))
#     all_participants = []
#     all_participants = client.get_participants(target_group, aggressive=True)

#     print('Saving In file...')
#     #print(target_group.title)
#     filename = target_group.title 
#     with open(("{}.csv".format(filename)),"w",encoding='UTF-8') as f:

#         writer = csv.writer(f,delimiter=",",lineterminator="\n")
#         writer.writerow(['username','user id', 'access hash','name','group', 'group id'])
#         for user in all_participants:
#             if user.username:
#                 username= user.username
#             else:
#                 username= ""
#             if user.first_name:
#                 first_name= user.first_name
#             else:
#                 first_name= ""
#             if user.last_name:
#                 last_name= user.last_name
#             else:
#                 last_name= ""
#             name= (first_name + ' ' + last_name).strip()
#             writer.writerow([username,user.id,user.access_hash,name,target_group.title, target_group.id])      
#     print('Members scraped successfully from {} .'.format(filename))

# chat_list_index = list(range(len(chats)))

# for x in chat_list_index:
#     try: 
#         get(x)
#     except:
#         print("No more groups.", end = " ")
# print("Done")