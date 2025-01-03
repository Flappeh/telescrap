from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest, GetMessagesRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser, Channel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
from .Database import TeleGroup
import random
from modules.Utils import get_logger, update_groups,  get_group_details, get_saved_dest
from .Environment import API_ID, API_HASH, PHONE_NUM
import asyncio
from time import sleep

logger = get_logger(__name__)

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
        self.PHONE_NUM = PHONE_NUM
        self.client : TelegramClient = None
        self.sent_code = False
        self.auth_data : ScraperAuth = ScraperAuth()
        
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
        self.client = TelegramClient(PHONE_NUM, API_ID, API_HASH)
        await self.client.connect()
        if not await self.client.is_user_authorized():
            logger.debug("Client not logged in yet")
            if self.sent_code == False:
                code_req = await asyncio.wait_for(self.client.send_code_request(PHONE_NUM),10)
                self.auth_data.code_hash = code_req.phone_code_hash
                self.sent_code = True
                self.auth_data.status = "sent_code"
                return self.auth_data
        self.auth_data.status = "done"
        return self.auth_data
    
    async def get_group_details(self, idx) -> TeleGroup:
        data = get_group_details(idx)
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
        data = get_saved_dest()
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
        update_groups(groups)
    
    async def get_telegram_message(self):
        # entity = await self.client.get_entity("777000")
        # async for message in self.client.iter_messages(entity, limit=200):
        #     print(message.text)
        dialog = await self.client.get_entity()
        async for dialog in self.client.iter_dialogs(limit=100):
            messages = await self.client.get_messages(dialog.entity, limit=10)
            for message in messages:
                try:
                    if "Do not give this code" in message.message:
                        print(f"From : {message.message}")
                        print(dialog)
                        print(message)
                except:
                    continue
    async def fetch_participants(self, group: TeleGroup):
        members = []
        logger.info("Proses ambil data user dari group")
        data = await self.client.get_participants(group.id,aggressive=True)
        for i in data:
            try:
                members.append((i.id,i.access_hash))
            except:
                continue
        return members      
    
    async def start_add_users(self,group,members):
        logger.info("Mulai menambah user ke group")
        n = 0
        group_id = group.id
        # for idx in range(0,len(members)-1,5):
        for member in members:
            n += 1
            if n == 10:
                break
            if n % 50 == 0:
                sleep(1)
            try:
                # users_to_add = []
                # stop = idx + 5 
                # if len(members) < stop:
                #     stop = len(members)
                # print(f"Stop : {stop}")
                
                # while idx < stop:
                #     users_to_add.append(InputPeerUser(members[idx][0], members[idx][1]))
                #     idx+=1
                
                users_to_add = InputPeerUser(member[0], member[1])
                # print(f"Users are : {users_to_add}")
                await self.client(InviteToChannelRequest(group_id, [users_to_add]))
                # await self.client(InviteToChannelRequest(group_id, [users_to_add]))
                logger.info("Waiting for 5-10 seconds")
                sleep(random.randrange(5, 10))
                logger.info("Done inviting users")
            except PeerFloodError:
                logger.error("[!] Getting Flood Error from telegram. \n[!] Script is stopping now. \n[!] Please try again after some time.")
                return "flood_error"
            except UserPrivacyRestrictedError:
                logger.error("[!] The user's privacy settings do not allow you to do this. Skipping.")
                continue
            except Exception as e:
                logger.error(f"[!] Unexpected Error, {e}")
                continue
        logger.info("Done adding users")
        return "done"
                
    async def start_scrape_group(self, group: TeleGroup):
        logger.info(f"Mulai proses scrape group data untuk group : {group.title}")
        members = await self.fetch_participants(group)
        result = await self.start_add_users(group, members)
        return result
    
async def get_scraper():
    bot = ScraperBot()
    await bot.create_client()
    return bot   

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