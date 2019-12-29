import sys
import logging
from time import sleep
from settings import settings
from helper.action import download_photo
from model.model import MediaObject


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

media = MediaObject.select().where(MediaObject.downloaded == False).limit(12)

for m in media:
    sleep(settings.sleep_between_requests)
    filename = str(m.user.user_id) + "." + str(m.media_id)
    success = download_photo(m.media_high_res_url, filename)

    if success:
        log.info("Download of %s successful" % filename)
