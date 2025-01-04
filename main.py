from modules.Utils import get_logger, init_program
from modules.TeleBot import TelegramBot


logger = get_logger(__name__)


def main():
    init_program()
    TeleBot = TelegramBot()
    TeleBot.start_bot()
    

if __name__ == "__main__":
    main()