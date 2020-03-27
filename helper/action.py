from settings import settings
import urllib.request
import subprocess
import requests


def download_photo(img_url, filename):
    # Create file
    filepath = "%s%s.jpg" % (settings.data_path, filename)
    f = open(filepath, 'wb')
    f.close()
    if img_url[:5] == "https":
        img_url = "http" + img_url[5:]
    try:
        urllib.request.urlretrieve(img_url, filepath)
    except urllib.request.ContentTooShortError:
        return False
    return True


class Telegram:
    BASE_URL = "https://api.telegram.org/bot%s/"

    def __init__(self, key):
        self.api_key = key
        self.BASE_URL = self.BASE_URL % key

    def send(self, chat: str, message: str):
        action = self.BASE_URL + "sendMessage?chat_id=%s&text=%s" % (chat, message)
        requests.get(action)

    def send_image(self, chat: str, imagepath: str):
        command = 'curl -s -X POST ' + self.BASE_URL + 'sendPhoto -F chat_id=' + chat + " -F photo=@" + imagepath
        subprocess.call(command.split(' '))
        return
