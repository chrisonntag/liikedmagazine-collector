import re, sys
from time import sleep
import logging
from igramscraper.instagram import Instagram
from peewee import fn, IntegrityError
from model.model import User, MediaObject, DATABASE
from settings import settings
from random import choice, uniform
from helper.parser import *


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


scraping_account = choice(range(1, len(settings.accounts) + 1))
scraping_user = settings.accounts[scraping_account]

logging.info("Logging in with username %s" % scraping_user.get('username'))

instagram = Instagram(sleep_between_requests=settings.sleep_between_requests)
instagram.with_credentials(
    scraping_user.get('username'),
    scraping_user.get('password'),
    'data/'
)
instagram.set_account_medias_request_count(12)  # media objects in a single request
instagram.set_user_agent(scraping_user.get('user_agent'))
instagram.login()

count = [1, 2, 3]
small_wait_time = uniform(0.6, 2)
middle_wait_time = uniform(2, 3)
long_wait_time = uniform(3, 5)


def mimic_activity():
    logging.info("Wait for %d seconds" % long_wait_time)
    sleep(long_wait_time)

    if should_do_action(settings.like_probability):
        tag = choice(scraping_user.get('interests'))
        logging.info("Today we like something from #%s" % tag)

        top_media = instagram.get_current_top_medias_by_tag_name(tag)

        for tm in top_media:
            instagram.like(tm.identifier)
            print("%s liked https://www.instagram.com/p/%s" % (scraping_user.get('username'), tm.short_code))
            sleep(long_wait_time)

            # Follow this user
            if should_do_action(settings.follow_probability):
                instagram.follow(tm.owner.identifier)
                print("%s started following user with id %s" % (scraping_user.get('username'), tm.owner.identifier))


"""
Scrape some user data

1. Get a user from the database, either the user with smallest progress (breadth search) or a user with a 
high progress (deep search). However on non parallelised bots choosing high progress would mean finishing one 
account completely and then switching to another.
2. Get media
    - Update user data
    - Update user model with new max id and progress
    - Populate media model
    - Find tagged users and create a new user (with parent linked)
"""

sleep(middle_wait_time)

user = User.select().where(User.progress < 0.95).order_by(User.progress.asc()).get()
media = instagram.get_medias_by_user_id(str(user.user_id), settings.media_per_request, user.max_id)
account = instagram.get_account_by_id(str(user.user_id))

# Update basic user data
user.username = account.username
user.follower = account.followed_by_count
user.following = account.follows_count
user.posts = account.media_count
user.max_id = instagram.user_media_progress[str(user.user_id)]

if user.posts > 0:
    user.progress = (user.scraped + settings.media_per_request) / user.posts
    user.scraped = user.scraped + settings.media_per_request

user.save()
logging.debug(user)

for m in media:
    sleep(small_wait_time)
    if m.is_ad:
        # Don't save ads
        continue

    # Save this media
    logging.debug("Starting to save https://instagram.com/p/%s" % m.short_code)
    try:
        with DATABASE.atomic():
            image = MediaObject.create(
                user=user,
                media_id=m.identifier,
                media_high_res_url=m.image_high_resolution_url,
                short_code=m.short_code,
                posted=m.created_time,
                caption=m.caption,
                media_type=m.type
            )
    except IntegrityError:
        logging.warning("https://instagram.com/p/%s by %s has already been saved" % (m.short_code, user.username))
        continue

    # Find users that were tagged in the image or mentioned in the caption
    tagged = instagram.get_media_tagged_users_by_code(m.short_code)
    tagged = {item['user']['username']: item['user']['id'] for item in tagged}
    mentioned = re.findall(r'(?<![@\w])@(\w{1,25})', m.caption)

    # Merge mentioned and tagged users
    for u in mentioned:
        if u not in tagged.keys():
            sleep(small_wait_time)
            mentioned_user = instagram.get_account(u)
            tagged[u] = mentioned_user.identifier

    # Create new users with the current parent
    for tagged_username, tagged_user_id in tagged.items():
        logging.debug("Starting to save tagged user %s from parent %s" % (tagged_username, user.username))
        try:
            with DATABASE.atomic():
                tagged_user = User.create(
                    user_id=tagged_user_id,
                    username=tagged_username,
                    parent=user.user_id
                )
        except IntegrityError:
            logging.warning("%s has already been registered as a user; "
                            "double repost from parent %s" % (u['user']['username'], user.username))

