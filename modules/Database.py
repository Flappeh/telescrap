from peewee import *
import os
from datetime import datetime
from playhouse.sqliteq import SqliteQueueDatabase

DIRNAME = os.getcwd()

db = SqliteQueueDatabase(DIRNAME + '/data/database.db')

class TeleGroup(Model):
    order = IntegerField()
    id = IntegerField()
    title = CharField()
    access_hash = IntegerField()
    is_destination = BooleanField(default=False)
    
    class Meta:
        database = db


# class Members(Model):
#     phone = CharField()
#     password = CharField()
#     last_used =  DateTimeField(default=datetime.now())
#     class Meta:
#         database = db
    
