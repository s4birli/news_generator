from configparser import ConfigParser
from pymongo import MongoClient
from bson import ObjectId
import ssl
import datetime


class Connection:
    def __init__(self):
        config = ConfigParser()
        config.read('config.ini')
        self.conn = str(config['MONGODB']['connection_string'])
        self.client = MongoClient(
            self.conn, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
        self.db = self.client.ContentorDb

    def get_active_urls(self):
        return self.db.Urls.find({'isActive': True})

    def get_active_requests(self, url_id):
        return self.db.Requests.find({'urlId': url_id, 'isActive': True})

    def get_url(self, url):
        return self.db.Urls.find_one({'url': url, 'isActive': True})

    def exist(self, news_item):
        return self.db.RequestItems.find(news_item).count() == 0

    def get_forbidden_url_words(self):
        return self.db.ForbidenUrlWords.find({}, {"value": 1, "_id": 0})

    def add_request_items(self, news_item):
        # _news_item = {'guid': news_item.get('guid')}
        # if self.exist(_news_item):

        req_items = self.db.RequestItems.find_one(
            {'guid': news_item.get('guid')})
        if req_items is None:
            return self.db.RequestItems.insert(news_item)
        else:
            return req_items

    def remove_news_item(self, guid):
        self.db.RequestItems.delete_one({'guid': guid})

    def get_forbidden_words(self):
        return self.db.ForbiddenWords.find()

    def update_request_item(self, news_item):
        self.db.RequestItems.update_one({'guid': news_item.get('guid')}, {"$set": {
                                        "postId": news_item.get('postId'), "attachmentId": news_item.get('attachmentId')}})

    def find_request(self, news_item):
        return self.db.RequestItems.find_one(news_item)

    def request_update(self, news_item):
        self.db.RequestItems.update_one(
            news_item, {"$set": {"isPublished": True}})

    def updateLastUpdate(self, url):
        #url_item = self.get_url_by_id(url.get("_id"))
        self.db.Urls.update_one({"_id": ObjectId(url.get("_id"))}, {
                                "$set": {"lastUpdate": datetime.datetime.now()}})


def db():
    return Connection()
