"""Model module for the Learning Journal app."""

import datetime
from flask_bcrypt import generate_password_hash
from flask_login import UserMixin

from peewee import *

DATABASE = SqliteDatabase("journal.db")


class User(UserMixin, Model):
    id = AutoField()
    username = CharField(unique=True)
    password = CharField(max_length=100)
    god = BooleanField(default=False)

    class Meta:
        database = DATABASE

    @classmethod
    def create_user(cls, username, password, god):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    password=generate_password_hash(password),
                    god=god
                )
        except IntegrityError:
            # raise ValueError("User already exists.")
            pass


class Entry(Model):
    id = AutoField()
    user = ForeignKeyField(User, backref="entries")
    title = CharField(max_length=256)
    date = DateField(default=datetime.date.today)
    time_spent = TimeField()
    learned = TextField()
    resources = TextField()
    tags = CharField(max_length=1000)
    private = BooleanField(default=False)
    hidden = BooleanField(default=False)

    class Meta:
        database = DATABASE

    def tags(self):
        return (Tag
                .select()
                .join(EntryTag)
                .join(Entry)
                .where(Entry.id == self.id)
                )


class Tag(Model):
    name = CharField(max_length=256)

    class Meta:
        database = DATABASE

    def entries(self):
        return (Entry
                .select()
                .join(EntryTag)
                .join(Tag)
                .where(Tag.name ** self.name)
                .order_by(Entry.date.desc())
                )


class EntryTag(Model):
    entry = ForeignKeyField(Entry)
    tag = ForeignKeyField(Tag)

    class Meta:
        database = DATABASE


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Entry, Tag, EntryTag], safe=True)
    DATABASE.close()
