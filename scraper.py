import re
import sys
from time import sleep
import logging
from helper.action import download_photo
from igramscraper.instagram import Instagram
from igramscraper.exception import *
from peewee import IntegrityError
from model.model import User, MediaObject, DATABASE
from settings import settings
from random import choice, uniform
from helper.parser import *


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


scraping_account = choice(range(1, len(settings.accounts) + 1))
scraping_user = settings.accounts[scraping_account]

log.info("Logging in with username %s" % scraping_user.get('username'))

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
    log.info("Wait for %d seconds" % long_wait_time)
    sleep(long_wait_time)

    if should_do_action(settings.like_probability):
        tag = choice(scraping_user.get('interests'))
        log.info("Today we like something from #%s" % tag)

        top_media = instagram.get_current_top_medias_by_tag_name(tag)

        for tm in top_media:
            if should_do_action(0.05):
                sleep(long_wait_time)

                # Follow this user
                if should_do_action(settings.follow_probability):
                    instagram.follow(tm.owner.identifier)
                    print("%s started following user with id %s" % (scraping_user.get('username'), tm.owner.identifier))


def do_scraping():
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

    user = User.select().where(User.progress < 0.95).order_by(User.progress.desc()).get()
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
    log.info("Crawl data from %s" % user.username)

    for m in media:
        log.info("--------------------------------------------")
        log.info("Starting to save https://instagram.com/p/%s" % m.short_code)
        sleep(small_wait_time)
        if m.is_ad or m.type != "image":
            log.info("Crawled media is an ad or no image.")
            continue

        # Find users that were tagged in the image or mentioned in the caption
        tagged = instagram.get_media_tagged_users_by_code(m.short_code)
        tagged = {item['user']['username']: item['user']['id'] for item in tagged}
        mentioned = re.findall(r'(?<![@\w])@(\w{1,25})', m.caption)

        # Load user accounts for tagged users
        for u in tagged.keys():
            sleep(small_wait_time)
            try:
                mentioned_user = instagram.get_account(u)

                # Don't add users with no posts
                if mentioned_user.media_count > 0:
                    tagged[u] = mentioned_user
            except InstagramNotFoundException:
                log.warning("Could not get user %s tagged in an image from %s" % (u, user.username))

        # Merge mentioned and tagged users
        for u in mentioned:
            log.info("Load data for tagged user %s" % u)
            if u not in tagged.keys() and u is not None:
                sleep(small_wait_time)
                try:
                    mentioned_user = instagram.get_account(u)

                    # Don't add users with no posts
                    if mentioned_user.media_count > 0:
                        tagged[u] = mentioned_user
                except InstagramNotFoundException:
                    log.warning("Could not get user %s tagged in an image from %s" % (u, user.username))

        # Create new users with the current parent
        for tagged_username, tagged_user_account in tagged.items():
            if tagged_username == user.username:
                # Go to next if a user tagged himself
                continue

            log.info("Save tagged user %s from parent %s" % (tagged_username, user.username))
            try:
                with DATABASE.atomic():
                    tagged_user = User.create(
                        user_id=tagged_user_account.identifier,
                        username=tagged_username,
                        parent=user.user_id,
                        follower=tagged_user_account.followed_by_count,
                        following=tagged_user_account.follows_count,
                        posts=tagged_user_account.media_count
                    )
            except IntegrityError:
                log.warning("%s has already been registered as a user; "
                            "double repost from parent %s" % (tagged_username, user.username))

        # Save this media
        if user.follower < 1:
            follower = 1
        else:
            follower = user.follower

        # Download this media
        f_name = str(user.user_id) + "." + str(m.identifier)
        download_successful = download_photo(m.image_high_resolution_url, f_name)

        try:
            with DATABASE.atomic():
                image = MediaObject.create(
                    user=user,
                    media_id=m.identifier,
                    media_high_res_url=m.image_high_resolution_url,
                    short_code=m.short_code,
                    posted=m.created_time,
                    downloaded=download_successful,
                    caption=m.caption,
                    mentions=len(tagged),
                    media_type=m.type,
                    like_ratio=m.likes_count/follower,
                    comment_ratio=m.comments_count/follower
                )
        except IntegrityError:
            log.warning("https://instagram.com/p/%s by %s has already been saved" % (m.short_code, user.username))
            continue


if __name__ == '__main__':
    for i in range(0, 6):
        if should_do_action(0.2):
            mimic_activity()

        do_scraping()
        sleep(uniform(50, 150))

