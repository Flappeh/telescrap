from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackContext, ConversationHandler, Defaults
from typing import List
from .Environment import BOT_TOKEN, BOT_NAME
import datetime
from telegram.error import NetworkError
from modules.MemberScraper import ScraperBot
import sys
import pytz
from modules.Utils import get_logger


logger = get_logger(__name__)

# State for setup_bot input

INIT, CODE = range(2)


class TelegramBot():
    def __init__(self):
        self.TOKEN = BOT_TOKEN
        self.bot_name = BOT_NAME
    
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

/setup\\_bot \\- setup scraper bot untuk bisa login

/list\\_groups \\- list semua group yang dapat di scrape

/set\\_destination *<group\\-url\\>* \\- Set tujuan group untuk member yang di add

/start\\_scrape *<group\\-id\\>* \\- Mulai proses add user dari group id yang dipilih
    """,
        parse_mode=ParseMode.MARKDOWN_V2)
    
    async def setup_bot_command(self, update: Update, context: CallbackContext):
        if self.check_time(update):
            return
        await update.message.reply_text("Mohon cek message di telegram dan reply dengan kode yang dikirim!")
        Scraper = ScraperBot()
        status = Scraper.create_client()
        if status == "done":
            await update.message.reply_text("Client sudah login, setup sudah tidak diperlukan")
            return ConversationHandler.END
        context.user_data['client'] = Scraper
        return INIT
    
    async def setup_get_code(self, update: Update, context: CallbackContext) -> int:
        data = update.message.text
        scraper : ScraperBot = context.user_data['client']
        status = scraper.create_client()
        if status == "need_login":
            scraper.login_client(data)
        await update.message.reply_text("Done setting up bot")
        return ConversationHandler.END
        
    
    async def cancel(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("Setup telah di cancel")
        return ConversationHandler.END    
    
    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")    

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
        sys.exit()

    def start_bot(self):
        builder = Application.builder()
        builder.token(self.TOKEN)
        builder.defaults(Defaults(tzinfo=pytz.timezone('Asia/Jakarta')))
        app = builder.build()
        
        logger.info("INITIALIZING Telegram Pi Wallet Bot")

        # Conversation Handler
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('setup_bot', self.setup_bot_command )],
            states={   
                INIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.setup_get_code)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )


        # Command
        app.add_handler(CommandHandler('start', self.start_command))
        app.add_handler(CommandHandler('help', self.help_command))
        app.add_handler(conv_handler)
        # Messages
        app.add_handler(MessageHandler(filters.TEXT, self.handle_message))
        
        # Errors
        app.add_error_handler(self.handle_error)
        
        logger.info("BOT RUNNING")
        app.run_polling(poll_interval=3)
        