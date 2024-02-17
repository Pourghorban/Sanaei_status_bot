from peewee import *
from Entities.database import db
from .user import User


class Inbounds(Model):
    user = ForeignKeyField(User, backref='inbounds')
    port = CharField()
    remark = CharField()

    class Meta:
        database = db
