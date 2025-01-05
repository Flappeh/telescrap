from modules.utils.common import get_logger
from modules.utils.utils import init_program, get_main_tele_account
from modules.telebot import TelegramBot
from modules.memberscraper import ScraperBot
import asyncio
logger = get_logger(__name__)

    
def main():
    init_program()
    TeleBot = TelegramBot()
    TeleBot.start_bot()
    

if __name__ == "__main__":
    main()