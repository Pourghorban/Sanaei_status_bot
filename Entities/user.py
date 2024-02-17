from peewee import *
from Entities.database import db


class User(Model):
    telegram_id = CharField(unique=True)

    class Meta:
        database = db


# class inbound(Model):
#     user = ForeignKeyField(User, backref='inbound')
#     port = CharField()
#     remark = CharField()
#
#     class Meta:
#         database = db
