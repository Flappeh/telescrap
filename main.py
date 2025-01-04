from modules.Utils import get_logger, init_program, get_main_tele_account
from modules.TeleBot import TelegramBot
from modules.MemberScraper import ScraperBot
import asyncio
logger = get_logger(__name__)

    
def main():
    init_program()
    # TeleBot = TelegramBot()
    # TeleBot.start_bot()
    

if __name__ == "__main__":
    main()