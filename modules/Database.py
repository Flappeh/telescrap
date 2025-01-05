from peewee import *
import os
from datetime import datetime
from playhouse.sqliteq import SqliteQueueDatabase

DIRNAME = os.getcwd()

db = SqliteQueueDatabase(DIRNAME + '/data/database.db')

class TeleGroup(Model):
    url = CharField()
    title = CharField()
    private = BooleanField(default=False)
    is_destination = BooleanField(default=False)
    
    class Meta:
        database = db

class TeleAccount(Model):
    PHONE_NUM = CharField()
    is_active = BooleanField(default=False)
    logged_in = BooleanField(default=False)
    is_main = BooleanField(default=False)
    
    class Meta:
        database = db
    
class TeleMember(Model):
    username = CharField()
    user_id = CharField()
    access_hash = CharField()
    group = CharField()
    group_id = CharField()
    
    class Meta:
        database = db
    
