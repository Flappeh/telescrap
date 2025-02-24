from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackContext, ConversationHandler, Defaults
from typing import List
from modules.environment import BOT_TOKEN, BOT_NAME
import datetime
from telegram.error import NetworkError
from modules.memberscraper import ScraperBot, get_scraper
import sys
import pytz
from modules.utils.common import get_logger
from modules.utils import utils
import asyncio

logger = get_logger(__name__)

# State for setup_bot input

IS_PRIVATE, CHANGE_DEST, PICK_DEST,  CONFIRM_DEST = range(4)
PICK_SCRAPE, CONFIRM_SCRAPE = range(2)

class TelegramBot():
    def __init__(self):
        self.TOKEN = BOT_TOKEN
        self.bot_name = BOT_NAME
        self.scraper : ScraperBot = None
    
    def check_time(self, update: Update) -> bool:
        if update.message.date.timestamp() < datetime.datetime.now().timestamp() - 1200:
            return True
        return False

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.check_time(update):
            return
        await update.message.reply_text("""
    *Group Scraper Bot*
    
Welcome to group scraper bot, please run \\/help to get to know availabile commands\\!
    """,
        parse_mode=ParseMode.MARKDOWN_V2)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Help text")
        else:
            if self.check_time(update):
                return
            await update.message.reply_text("""
    *Group Scraper Bot*

Command yang dapat dilakukan:

/help \\- Show command ini

/set\\_destination \\- Set tujuan group untuk member yang di add

/start\\_scrape \\- Mulai proses add user dari group id yang dipilih
    """,
        parse_mode=ParseMode.MARKDOWN_V2)
    
        
    async def cancel(self,update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("Setup telah di cancel")
        return ConversationHandler.END    

    async def start_scrape_command(self, update: Update, context: CallbackContext):
        if self.check_time(update):
            return
        
        if self.scraper == None:
            self.scraper, auth = await get_scraper()
            if auth.status != "done":
                await update.message.reply_text("User hasn't logged in yet, please setup using /setup_bot")
                return ConversationHandler.END
            
        saved_dest = utils.get_saved_dest()
        
        if saved_dest == None:
            await update.message.reply_text("Group tujuan belum di setup. Mohon lakukan /set_destination")
            return ConversationHandler.END
        
        context.user_data['scraper'] = self.scraper
        context.user_data['group_dest'] = saved_dest
        
        await update.message.reply_text("Kirim url group yang ingin di scrape")
        
        return PICK_SCRAPE

    async def pick_scrape_server(self, update: Update, context: CallbackContext):
        data = update.message.text
        try:
            dest_group = context.user_data['group_dest']
            if data == dest_group.url:
                await update.message.reply_text("url group yang akan di scrape sama dengan group tujuan, mohon pilih ulang")
                return PICK_SCRAPE
            scrape_source = await self.scraper.client.get_entity(data)
            
            if scrape_source == None:
                await update.message.reply_text("Invalid url, mohon kirim ulang url yang valid!")
                return PICK_SCRAPE
            
            context.user_data['scrape_source'] = scrape_source
            context.user_data['scrape_source_url'] = data
            message = (f"Group yang dipilih untuk scrape :\n<b>{scrape_source.title}</b>\n\n"+
                       f"Group yang dituju :\n<b>{dest_group.title}</b>\n\n"+
                       "Apakah pilihan sudah benar? (y/n)"
                       )
            await update.message.reply_text(message, ParseMode.HTML)
            return CONFIRM_SCRAPE
        except:
            await update.message.reply_text("Terjadi error saat memilih server, mohon coba lagi")
            return ConversationHandler.END
    
    async def confirm_scrape_server(self, update: Update, context: CallbackContext):
        if self.check_time(update):
            return
        data = update.message.text.lower()
        chat_id = update.message.chat.id
        try:
            if data != 'y' and data != 'n':
                await update.message.reply_text("Mohon konfirmasi dengan reply y atau n")
                return CONFIRM_SCRAPE
            if data == 'n':
                await update.message.reply_text("Batal untuk mengganti group destination")
                return ConversationHandler.END
            
            scrape_source = context.user_data['scrape_source_url']
            dest_group = context.user_data['group_dest']
            
            await update.message.reply_text("Proses scrape data dimulai, mohon menunggu...")
            
            grp_entity = await self.scraper.client.get_entity(scrape_source)
            
            members = await self.scraper.fetch_and_store_members(grp_entity)
            
            await self.scraper.client.disconnect()
            del self.scraper
            self.scraper = None

            utils.start_scrape_process(dest_group, scrape_source, members)
            # result = await self.scraper.start_scrape_group(scrape_source)
            
            await context.bot.send_message(chat_id=chat_id, text = "Proses scrape data telah diperintahkan! Mohon cek group anda")
            return ConversationHandler.END
        
        
        except Exception as e:
            logger.error(f"Error terjadi saat konfirmasi scrape server, log : {e}")
            await update.message.reply_text("Terjadi error saat konfirmasi scrape server. Mohon ulangi")
            return ConversationHandler.END
    
    async def set_destination_command(self, update: Update, context: CallbackContext):
        if self.check_time(update):
            return
        
        if self.scraper == None:
            self.scraper, auth = await get_scraper()
            if auth.status != "done":
                await update.message.reply_text("User hasn't logged in yet, please setup using /setup_bot")
                return ConversationHandler.END
            
        saved_dest = await self.scraper.check_saved_dest()
        if saved_dest:
            await update.message.reply_text(f"Destination sudah pernah di setup!\nGroup tujuan saat ini : {saved_dest.title}\nApakah ingin mengganti? (y/n)")
            context.user_data['group_dest'] = saved_dest
            return CHANGE_DEST
        await update.message.reply_text("Apakah tujuan private? (y/n)")
        return IS_PRIVATE
    
    async def change_destination(self, update: Update, context: CallbackContext):
        if self.check_time(update):
            return
        data = update.message.text.lower()
        try:
            if data != 'y' and data != 'n':
                await update.message.reply_text("Mohon konfirmasi dengan reply y atau n")
                return CHANGE_DEST
            if data == 'n':
                await update.message.reply_text("Batal untuk mengganti group destination")
                return ConversationHandler.END
            
            await update.message.reply_text("Apakah tujuan private? (y/n)")
            return IS_PRIVATE
            
        except:
            await update.message.reply_text("Terjadi error saat mengganti destinasi, mohon coba ulang")
            return ConversationHandler.END
          
    async def is_private_destination(self, update: Update, context: CallbackContext):
        if self.check_time(update):
            return
        data = update.message.text.lower()
        try:
            if data != 'y' and data != 'n':
                await update.message.reply_text("Mohon konfirmasi dengan reply y atau n")
                return IS_PRIVATE
            if data == 'n':
                await update.message.reply_text("Group tujuan adalah public")
                context.user_data['private'] = False
            else:
                await update.message.reply_text("Group tujuan adalah private")
                context.user_data['private'] = True
            await update.message.reply_text("Kirim url group yang akan jadi tujuan")
            return PICK_DEST
        except:
            await update.message.reply_text("Jawaban tidak dikenal, mohon reply dengan 'y' atau 'n' ")
            return IS_PRIVATE
          
    async def pick_destination(self, update: Update, context: CallbackContext):
        url = update.message.text
        try:
            group_data = await self.scraper.client.get_entity(url)
            if group_data == None:
                raise
            await update.message.reply_text(f"Group yang dipilih : \n{group_data.title},\nApakah pilihan sudah benar? (y/n)")
            context.user_data['group_dest'] = group_data
            context.user_data['group_url'] = url
            
            return CONFIRM_DEST
        except:
            await update.message.reply_text("Url yang dikirim tidak dikenal, mohon ulangi")
            return PICK_DEST
    
    async def confirm_destination(self, update: Update, context: CallbackContext):
        data = update.message.text.lower()
        try:
            if data != 'y' and data != 'n':
                await update.message.reply_text("Mohon konfirmasi dengan reply y atau n")
                return CONFIRM_DEST
            if data == 'n':
                await update.message.reply_text("Set group destination dibatalkan")
                return ConversationHandler.END
            
            group_dest = context.user_data['group_dest']
            url = context.user_data['group_url']
            
            dest = {
                "url": url,
                "title": group_dest.title,
                "private": context.user_data['private']
            }
            
            result = utils.set_group_destination(dest)
            
            if result == False:
                await update.message.reply_text("Terjadi error saat setup destinasi, mohon coba kembali")
                return ConversationHandler.END
            await update.message.reply_text(f"Group tujuan telah dikonfirmasi\nName:  {group_dest.title}")
            
            self.scraper.client.disconnect()
            del self.scraper
            self.scraper = None
            return ConversationHandler.END
        
        except:
            await update.message.reply_text("Terjadi error saat konfirmasi destinasi group. Mohon coba ulang")
            return ConversationHandler.END
             
    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I don't understand that command.")    

    def handle_response(self, text: str) -> str:
        # This is the logic for processing the request
        string_content: str = text.lower()
        
        if 'hello' in string_content:
            return "Hello"
        if 'test' in string_content:
            return "Test triggered"
        return "Nothing known"

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.check_time(update):
            return
        message_type: str = update.message.chat.type # Group or Private Chat
        text: str = update.message.text
        
        logger.debug(f"User: ({update.message.chat.id}) in {message_type} sent: {text}")
        
        if message_type == 'group':
            if self.bot_name in text:
                new_text: str = text.replace(self.bot_name, '').strip()
                response: str = self.handle_response(new_text)
            else:
                return
        else: 
            response: str = self.handle_response(text)
        
        logger.debug(response )
        await update.message.reply_text(response)
        
    # async def stop()
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Update {update} caused error : {context.error}")
        context.application.updater.stop()
        context.application.stop()
        context.application.shutdown()
        utils.release_all_tele_account()
        sys.exit()

    def start_bot(self):
        builder = Application.builder()
        builder.token(self.TOKEN)
        builder.defaults(Defaults(tzinfo=pytz.timezone('Asia/Jakarta')))
        app = builder.build()
        
        logger.info("INITIALIZING Telegram Pi Wallet Bot")

        # Conversation Handler
        
        conv_handler = ConversationHandler(
            entry_points=[
                          CommandHandler('set_destination', self.set_destination_command )],
            states={   
                IS_PRIVATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.is_private_destination)],
                PICK_DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.pick_destination)],
                CHANGE_DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.change_destination)],
                CONFIRM_DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_destination)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        scrape_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start_scrape', self.start_scrape_command )],
            states={   
                PICK_SCRAPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.pick_scrape_server)],
                CONFIRM_SCRAPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_scrape_server)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )


        # Command
        app.add_handler(CommandHandler('start', self.start_command))
        app.add_handler(CommandHandler('help', self.help_command))
        app.add_handler(conv_handler)
        app.add_handler(scrape_conv_handler)
        # Messages
        app.add_handler(MessageHandler(filters.TEXT, self.handle_message))
        
        # Errors
        app.add_error_handler(self.handle_error)
        
        logger.info("BOT RUNNING")
        try:
            app.run_polling(close_loop=False,poll_interval=3)
        except Exception as e:
            logger.error("Error occured on telegram bot loop")
            logger.error(f"Message : {e}")
            