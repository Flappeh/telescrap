from modules.Utils import get_logger
from modules.TeleBot import TelegramBot


logger = get_logger(__name__)


def main():
    TeleBot = TelegramBot()
    TeleBot.start_bot()
    

if __name__ == "__main__":
    main()