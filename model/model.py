import datetime
from peewee import *
from settings import settings


DATABASE = SqliteDatabase("labeled_media.db")


class User(Model):
    user_id = IntegerField(unique=True, primary_key=True)
    username = CharField()
    follower = IntegerField(null=True, default=None)
    following = IntegerField(null=True, default=None)
    posts = IntegerField(null=True, default=None)
    progress = FloatField(default=0.0)
    parent = IntegerField(null=True, default=None)
    max_id = TextField(default="")

    class Meta:
        database = DATABASE


class MediaObject(Model):
    user = ForeignKeyField(User, backref='images')
    media_id = IntegerField()
    media_high_res_url = CharField(null=True)
    short_code = CharField()
    posted = DateTimeField()
    created = DateTimeField(default=datetime.datetime.now)

    quality = BooleanField(null=True, default=None)  # 1 or 0 for high or low quality
    caption = TextField(null=True)
    mentions = IntegerField(null=True)  # number of mentions in the caption
    hashtags = IntegerField(null=True)  # number of hashtags
    media_type = CharField(null=True)  # either image, video, carousel, ...
    view_ratio = FloatField(null=True)  # views on a video / followers
    like_ratio = FloatField(null=True)  # likes / followers
    comment_ratio = FloatField(null=True)  # comments / followers

    class Meta:
        database = DATABASE
        primary_key = CompositeKey('user', 'media_id')


def fill():
    with DATABASE.atomic():
        for user_id, username in settings.sources.items():
            User.create(user_id=user_id, username=username)


DATABASE.create_tables([MediaObject, User])
