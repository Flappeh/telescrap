from modules.database import TeleAccount, TeleGroup
from modules.utils.common import get_logger
from modules.environment import API_HASH, API_ID
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, PhoneNumberBannedError, ChatAdminRequiredError
from telethon.errors.rpcerrorlist import ChatWriteForbiddenError, UserBannedInChannelError, UserAlreadyParticipantError, FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, AddChatUserRequest
from telethon.tl.functions.channels import JoinChannelRequest
from time import sleep
import random
import asyncio

logger = get_logger(__name__)


class AdderBot():
    def __init__(self, account: TeleAccount, group_source: str, grop_dest: dict, member_ids: list[str]):
        self.PHONE_NUM = account.PHONE_NUM
        self.account = account
        self.client = None
        self.group_src = group_source
        self.group_dest = grop_dest
        self.acc_name = ""
        self.group_src_entity = None
        self.group_dest_entity = None
        self.group_dest_details = None
        self.member_ids = [int(i) for i in member_ids]
        self.members = []
    
    def run(self):
        try:
            logger.info(f"Got process command for user : {self.account.PHONE_NUM}")
            asyncio.run(self.start_process())
        except Exception as e:
            logger.error(f"Error starting subprocess for account: {self.account.PHONE_NUM}, Details : {e}")
    async def start_process(self):
        try:
            self.client  = await self.connect()
            await self.join_scrape_source()
            await self.join_scrape_dest()
            await self.get_participants()
            await self.start_scrape_process()
        except:
            return
        
    async def connect(self):
        logger.info(f"Logging in to {self.PHONE_NUM}")
        try:
            client = TelegramClient(f"data/sessions/{self.PHONE_NUM}", API_ID, API_HASH)
            await client.start(self.PHONE_NUM)
            my_acc = await client.get_me()
            acc_name = my_acc.first_name
            self.acc_name = acc_name
            logger.info(f"Starting session with account: {acc_name}")
            if not await client.is_user_authorized():
                logger.error("Client not logged in yet, removing number")
                del self
                return None
            logger.info("Got client")
            return client
        except Exception as e:
            logger.error(f"Error occuren on login user. Details {e}")
            return None
    async def join_scrape_source(self):
        logger.info("Joining scrape source")
        print(self.group_src)
        if '/joinchat/' in self.group_src:
            group_hash = self.group_src.split('/joinchat/')[1]
            try:
                await self.client(ImportChatInviteRequest(group_hash))
                logger.info(f"User {self.acc_name} join group source scrape.")
            except UserAlreadyParticipantError:
                pass
        else:
            await self.client(JoinChannelRequest(self.group_src))
            logger.info(f"User {self.acc_name} join group source scrape.")
        try:
            logger.info("Getting group entity for source")
            self.group_src_entity = await self.client.get_entity(self.group_src)
        except:
            logger.error(f"Unable to get group entity for url :{self.group_src}")
    
    async def join_scrape_dest(self):
        logger.info(f"User {self.acc_name} joining to group destination")
        if not self.group_dest["private"]:
            try:
                await self.client(JoinChannelRequest(self.group_dest["url"]))
                group_dest_entity = await self.client.get_entity(self.group_dest["url"])
                self.group_dest_entity = group_dest_entity
                self.group_dest_details = InputPeerChannel(self.group_dest_entity.id, self.group_dest_entity.access_hash)
            except Exception as e:
                logger.error(f"Error joining to group destination, Details {e}")
        else:
            try:
                group_hash = self.group_dest["url"].split('/joinchat/')[1]
                await self.client(ImportChatInviteRequest(group_hash))
            except UserAlreadyParticipantError:
                pass
            self.group_dest_entity = await self.client.get_entity(self.group_dest["url"])
            self.group_dest_details = self.group_dest_entity

    async def get_participants(self):
        await self.client.get_dialogs()
        try:
            members = []
            members = await self.client.get_participants(self.group_src_entity,aggressive=False)
        except Exception as e:
            logger.error("Unable to scrape members")
            logger.error(f"Details : {e}")
            del self
        
        approx_member_count = len(members)
        assert approx_member_count != 0
        self.members = members

    async def start_scrape_process(self):
        logger.info("Start scraping process")
        adding_status = 0
        peer_flood_status = 0
        for user in self.members:
            if user.id not in self.member_ids:
                continue
            if peer_flood_status == 10:
                logger.error("Too many peer flood error, closing session")
                break
            try:
                if not self.group_dest["private"]:
                    await self.client(InviteToChannelRequest(self.group_dest_details, [user]))
                else:
                    await self.client(AddChatUserRequest(self.group_dest_details.id, user, 42))
                user_id = user.first_name
                group_title = self.group_dest["title"]
                logger.info(f"User {self.acc_name} -- {user_id} --> {group_title}")
                adding_status += 1
                logger.info("Sleeping for 20-30 seconds")
                sleep(random.randrange(20, 30))
            except UserPrivacyRestrictedError:
                logger.error(f'User Privacy Restricted Error')
                continue
            except PeerFloodError:
                logger.error(f' User: {self.acc_name} -- Peer Flood Error.')
                peer_flood_status += 1
                continue
            except ChatWriteForbiddenError:
                logger.error(f'Can\'t add to group. Contact group admin to enable members adding')
                break
            except UserBannedInChannelError:
                logger.error(f'User: {self.acc_name} -- Banned from writing in groups')
                break
            except ChatAdminRequiredError:
                logger.error(f'User: {self.acc_name} -- Chat Admin rights needed to add')
                break
            except UserAlreadyParticipantError:
                logger.error(f'User: {self.acc_name} -- User is already a participant')
                continue
            except FloodWaitError as e:
                logger.error(f'Error flood dicapai. Details: {e}')
                break
            except ValueError:
                logger.error(f'Terjadi error pada Entity')
                continue
            except KeyboardInterrupt:
                logger.error(f' ---- Adding Terminated ----')
            except Exception as e:
                logger.error(f'Error occured: {e}')
                continue
    