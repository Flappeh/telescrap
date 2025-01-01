from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import csv
from modules.Utils import get_logger
from .Environment import API_ID, API_HASH, PHONE_NUM


logger = get_logger(__name__)


class ScraperBot():
    def __init__(self):
        self.API_ID = API_ID
        self.API_HASH = API_HASH
        self.PHONE_NUM = PHONE_NUM
        self.client : TelegramClient = None
        self.sent_code = False
    
    def login_client(self, code: str):
        try:
            self.client.sign_in(PHONE_NUM, code)
        except:
            return False
        
    def create_client(self):
        self.client = TelegramClient(PHONE_NUM, API_ID, API_HASH)
        self.client.connect()    
        if not self.client.is_user_authorized():
            logger.debug("Client not logged in yet")
            if self.sent_code == False:
                self.client.send_code_request(PHONE_NUM)
                self.sent_code = True
                return "sent_code"
            else:
                return "need_login"
        return "done"
    
# client = TelegramClient(PHONE_NUM, API_ID, API_HASH)

# client.connect()
# if not client.is_user_authorized():
#     client.send_code_request(PHONE_NUM)
#     client.sign_in(PHONE_NUM, input('Enter the code: '))


# chats = []
# last_date = None
# chunk_size = 200
# groups=[]
 
# result = client(GetDialogsRequest(
#              offset_date=last_date,
#              offset_id=0,
#              offset_peer=InputPeerEmpty(),
#              limit=chunk_size,
#              hash = 0
#          ))
# chats.extend(result.chats)


# for chat in chats:
#     try:
#         if chat.megagroup== True:
#             groups.append(chat)
#     except:
#         continue
# print('Parsing the following groups:')
# i=0
# for g in groups:
#     print(str(i) + '- ' + g.title)
#     i+=1

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