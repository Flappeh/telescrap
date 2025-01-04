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

class TeleAccount(Model):
    API_ID = CharField(unique=True)
    API_HASH = CharField(unique=True)
    PHONE_NUM = CharField()
    is_active = BooleanField(default=False)
    
    class Meta:
        database = db
    
class TeleMember(Model):
    username = CharField(default="")
    user_id = CharField()
    access_hash = CharField()
    group = CharField()
    group_id = CharField()
    
    class Meta:
        database = db
    
