from news.news_generator import News
from data.mongodb import db
from image.remove import remove_images
from bson import ObjectId
import simplejson as json
import news
import time
import random


def main():
    while True:
        remove_images()
        with open("urls.txt", "rb") as json_data:
            url_list = json.load(json_data)

        for url in url_list:
            url_data = db().get_url(url)
            if url_data is not None:
                request_list = db().get_active_requests(
                    ObjectId(url_data['_id']))
                for request in request_list:
                    news = News(url_data, request)
                    news.scrab()

                db().updateLastUpdate(url_data)

        r = random.randrange(
            3*60, 8*60) if 6 <= time.localtime().tm_hour <= 23 else random.randrange(43*60, 68*60)
        time.sleep(r)


if __name__ == "__main__":
    main()
