from .Database import db, TeleGroup
from .Environment import init_env
from .Utils import init_logger

init_logger()
init_env()

db.connect()
db.create_tables([TeleGroup])