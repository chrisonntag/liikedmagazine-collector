from igramscraper.instagram import Instagram
from settings import settings
import re
from evaluation.quality_prediction import QualityPrediction
from model.model import MediaObject, User, Post, DoesNotExist
from random import choice, sample
from PIL import Image
import imagehash
from instapy_cli import client
import pandas as pd

"""
1. Select images with no quality set by a tagger. 
    - If there a none, load some by running the scraper service.
2. Check if the user has already been reposted
3. Do stuff like removing images with more than one mention, comments disabled, ad-keywords in the caption
4. Do prediction for each image and take a few of the highest scored with score at least >0.72
5. Check if image has already been posted with a perceptual hash algorithm like imagehash.
6. Generate a basic caption from a structure list.
7. Select a subset of hashtags related to the bots topic.
8. Post!
"""


def has_been_posted(imgh):
    """
    This checks if a picture with the same hash has already been posted.
    :param imgh: The image hash.
    :return: Whether a similar hash has been found in the posts table.
    """
    posts = Post.select().where(Post.imagehash == imgh).limit(1)
    return len(posts) > 0


def post(fn, o):
    caption = gen_caption(o)
    print("Filename:", fn)
    print("Caption:", "\n" + caption)

    with client(settings.bot_account['username'], settings.bot_account['password']) as cli:
        cli.upload(fn, caption=caption)

    Post.create(
        user=obj['user_id'],
        media_id=obj['media_id'],
        imagehash=imagehash,
        caption=caption
    )


def gen_filename(o):
    return "%s%s.%s.jpg" % (settings.data_path, o['user_id'], o['media_id'])


def gen_hashtags(num: int=12):
    if len(settings.tags) < num:
        num = len(settings.tags)
    return " ".join(sample(settings.tags, k=num))


def gen_caption(o):
    caption = choice(settings.caption_templates) % o['username']
    placeholder = "\n.\n.\n.\n"
    tags = gen_hashtags()

    return caption + placeholder + tags


def gen_hash(fn):
    try:
        return str(imagehash.phash(Image.open(fn), 8))
    except FileNotFoundError:
        print("Possible post file %s could not be found" % fn)
        return None


featured_users = [user.user_id for user in Post.select()]
query = MediaObject.select(
    MediaObject.media_id,
    MediaObject.short_code,
    MediaObject.caption,
    MediaObject.comment_ratio,
    MediaObject.like_ratio,
    MediaObject.mentions,
    MediaObject.quality,
    User.follower,
    User.following,
    User.posts,
    User.user_id,
    User.username
).join(User, on=(MediaObject.user_id == User.user_id)).where(
    MediaObject.quality.is_null(True),
    MediaObject.mentions < 2,
    MediaObject.user_id.not_in(featured_users)
)
objs = query.dicts()

qp = QualityPrediction()
quality_images = []

if len(objs) > 0:
    for obj in objs:
        if re.search(settings.ad_regex, obj['caption']):
            # This is probably an ad, check the next image.
            print("This is probably an ad: %s" % obj['short_code'])
            continue

        if obj['username'] in re.findall(settings.hashtag_regex, obj['caption']):
            # This is probably a post from a feature site, if the a user took his own username as a hashtag
            print("This is probably from a feature site: %s" % obj['short_code'])

        data = pd.DataFrame([obj])

        try:
            X = QualityPrediction.prepare_features(data, train=False)
            pred_proba = qp.predict_proba(X=X).item(1)  # Returns the probability for quality == 1

            if pred_proba >= 0.72:
                print("https://instagram.com/p/%s %.3f" % (obj['short_code'], pred_proba))
                quality_images.append(
                    (pred_proba, obj)
                )
        except FileNotFoundError:
            print("Could not load TFIDF Vocabulary files.")
else:
    print("No data available.")

# Sort the selected images in descending order (highest rating first).
quality_images = sorted(quality_images, key=lambda el: el[0], reverse=True)
posted = False
for pred, obj in quality_images:
    filename = gen_filename(obj)
    imagehash = '123ha672bc892'  # gen_hash(filename)
    posted_obj = False

    if imagehash is not None and not has_been_posted(imagehash) and not posted:
        # Post if image has not been posted before and set var that post image has been found.
        post(filename, obj)
        posted = True
        posted_obj = True

    # Update quality for all images except it's predicted quality is bigger than some threshold.
    if posted_obj or pred < 0.80:
        try:
            media_obj = MediaObject.get(user_id=obj['user_id'], media_id=obj['media_id'])
            media_obj.quality = pred
            media_obj.save()
        except DoesNotExist:
            print("The image does not exist in the database.")


