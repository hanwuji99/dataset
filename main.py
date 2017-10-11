# -*- coding: utf-8 -*-
from peewee import MySQLDatabase
from test import Database

connect_kwargs = {
    'charset': 'utf8mb4',
    'host': 'localhost',
    'port': 3306,
    'user': 'root'
}
db = Database(None)

db.init(**connect_kwargs)

#如果不传database,那么
# self.deferred为True
# self.database为None

# database = MySQLDatabase(None)
# db = Database(database,**connect_kwargs)

#如果传,那么是
# self.deferred为False
# self.database为一个对象　如：<peewee.MySQLDatabase object at 0x7f2ed3fc7250>

