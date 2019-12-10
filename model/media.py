import datetime
from peewee import *


DATABASE = SqliteDatabase("labeled_media.db")


class Image(Model):
    user_id = IntegerField(unique=True)
    username = CharField(unique=True)
    follower = IntegerField()
    image_url = CharField()
    post_url = CharField()
    posted = DateTimeField()
    created = DateTimeField(default=datetime.datetime.now)

    quality = BooleanField(null=True, default=None)  # 1 or 0 for high or low quality
    caption = TextField()
    mentions = IntegerField()  # number of mentions in the caption
    hashtags = IntegerField()  # number of hashtags
    media_type = CharField()  # either IMAGE or VIDEO
    view_ratio = FloatField()  # views on a video / followers
    like_ratio = FloatField()  # likes / followers
    comment_ratio = FloatField()  # comments / followers

    class Meta:
        database = DATABASE


DATABASE.create_tables([Image])
