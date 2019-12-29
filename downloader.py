import sys
import logging
from time import sleep
from settings import settings
from helper.action import download_photo
from model.model import MediaObject
from random import uniform


IMAGES_PER_ROUND = 12
ROUNDS = 19

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

for i in range(1, ROUNDS + 1):
    sleep(uniform(6,25))
    media = MediaObject.select().where(MediaObject.downloaded == False).limit(IMAGES_PER_ROUND)

    for m in media:
        sleep(0.3)
        filename = str(m.user.user_id) + "." + str(m.media_id)
        success = download_photo(m.media_high_res_url, filename)

        if success:
            log.info("Download of %s successful" % filename)
            m.downloaded = True
            m.save()
        else:
            log.info("There has been an issue with %s" % filename)
    log.info("Done %d of %d" % (i*IMAGES_PER_ROUND, IMAGES_PER_ROUND * (ROUNDS-1)))
    log.info("-----------------------------------")

