from modules.database import db, TeleGroup, TeleMember, TeleAccount
from modules.utils.common import init_logger

init_logger()

db.connect()
db.create_tables([TeleGroup, TeleMember, TeleAccount])