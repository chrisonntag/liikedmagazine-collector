from time import sleep
import logging
from igramscraper.instagram import Instagram
from peewee import fn
from model.model import User, MediaObject
from settings import settings
from random import choice, uniform
from helper.parser import *


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
wait_time = uniform(3, 5)


def mimic_activity():
    logging.info("Wait for %d seconds" % wait_time)
    sleep(wait_time)

    if should_do_action(settings.like_probability):
        tag = choice(scraping_user.get('interests'))
        logging.info("Today we like something from #%s" % tag)

        medias = instagram.get_medias_by_tag(tag, count=choice(count))

        for m in medias:
            instagram.like(m.identifier)
            print("%s liked https://www.instagram.com/p/%s" % (scraping_user.get('username'), m.short_code))
            sleep(wait_time)

            # Follow this user
            if should_do_action(settings.follow_probability):
                instagram.follow(m.owner.identifier)
                print("%s started following user with id %s" % (scraping_user.get('username'), m.owner.identifier))


"""
Scrape some user data

1. Get a user from the database, either the user with smallest progress (breadth search) or a user with a 
high progress (deep search). However on non parallelised bots choosing high progress would mean finishing one 
account completely and then switching to another.
2. Get media
    - Update user data
    - Populate media model
    - Find tagged users and create a new user (with parent linked)
    - Update user model with new max id and progress
"""
user = User.select().where(User.progress < 0.95).order_by(User.progress.asc()).get()
media = instagram.get_medias_by_user_id(str(user.user_id), 12, user.max_id)

for m in media:
    print(m.identifier)
    print(m.short_code)
    print(m.created_time)
    print(m.type)
    print(m.link)
    print(m.image_high_resolution_url)
    print(m.square_images)
    print(m.caption)
    print(m.is_ad)
    print(m.likes_count)
    print(m.comments_count)
    print("--Owner--")
    print(m.owner.identifier)
    print("-------------------------------------")
    if m.is_ad:
        continue

    image = MediaObject.create(
        user=user,
        media_id=m.identifier,
        media_high_res_url=m.image_high_resolution_url,
        short_code=m.short_code,
        posted=m.created_time,
        caption=m.caption,
        media_type=m.type
    )
