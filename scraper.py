from time import sleep
import logging
from igramscraper.instagram import Instagram
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
instagram.set_account_medias_request_count(30)  # media objects in a single request
instagram.set_user_agent(scraping_user.get('user_agent'))
instagram.login()

count = [1, 2, 3]
wait_time = uniform(3, 5)

logging.info("Wait for %d seconds" % wait_time)
sleep(wait_time)

if should_do_action(settings.like_probability):
    tag = choice(scraping_user.get('interests'))
    logging.info("Today we like something from #%s" % tag)

    medias = instagram.get_medias_by_tag(tag, count=choice(count))

    for media in medias:
        instagram.like(media.identifier)
        print("%s liked https://www.instagram.com/p/%s" % (scraping_user.get('username'), media.short_code))
        sleep(wait_time)

        # Follow this user
        if should_do_action(settings.follow_probability):
            instagram.follow(media.owner.identifier)
            print("%s started following user with id %s" % (scraping_user.get('username'), media.owner.identifier))

"""
Scrape some user data

1. Get a user from the database
"""
