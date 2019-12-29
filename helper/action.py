from settings import settings
import urllib.request


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
