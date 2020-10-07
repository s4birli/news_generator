from wordpress_xmlrpc import Client
from wordpress_xmlrpc.methods.posts import GetPosts, GetPost, NewPost, EditPost
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.compat import xmlrpc_client
from image.image_process import upload_image
from image.remove import remove_images
from keyworder import keyworder
from data.mongodb import db
from datetime import date
import time


class WordPress(object):
    def __init__(self, url):
        self.url = url
        self._url = "{}/{}".format(url.get('url'), "xmlrpc.php")
        self.user_name = url.get('userName')
        self.password = url.get('password')
        self.client = Client(self._url, self.user_name, self.password)

    def get_latest_post_by_category(self, category):
        offset = 0
        increment = 20
        while True:
            try:
                time.sleep(3)
                posts = self.client.call(GetPosts(
                    {'post_status': 'publish', 'orderby': 'post_modified', 'order': 'DESC', 'number': increment, 'offset': offset}))
                if len(posts) == 0:
                    return None  # no more posts returned

                for post in posts:
                    for terms in post.terms:
                        if terms.taxonomy == 'category':
                            if terms.name in category:
                                return post

                offset = offset + increment
            except Exception as e:
                print(e)

    def update_post(self, news_item):
        try:
            post = self.client.call(GetPost(news_item['postId']))
            if len(news_item.get('attachmentId')) > 0:
                post.thumbnail = news_item.get('attachmentId')

            self.client.call(EditPost(post.id, post))
        except Exception as e:
            print(e)

    def publish_article(self, news_item):
        try:
            if news_item["spinnedText"] is None:
                db().remove_news_item(news_item.get('guid'))
                return False

            attachment = upload_image(self.url, news_item)

            if attachment is not None:
                news_item['attachmentId'] = attachment['id']

            focus = keyworder.get_focus(news_item.get(
                'title'), news_item.get('keywords'))

            yoast = [{'key': '_yoast_wpseo_opengraph-title', 'value': news_item.get('title')},
                     {'key': '_yoast_wpseo_twitter-title',
                         'value': news_item.get('title')},
                     {'key': 'post-feature-caption',
                         'value': news_item.get('title')},
                     {'key': 'twitterCardType', 'value': 'summary_large_image'},
                     {'key': '_yoast_wpseo_focuskw', 'value': focus},
                     {'key': 'sub-title',
                         'value': news_item.get('spinnedText')[:215]},
                     {'key': 'meta_description', 'value': news_item.get('spinnedText')[
                         :215]},
                     {'key': 'mt_description', 'value': news_item.get('spinnedText')[:215]}]

            if attachment is not None:
                yoast.append({'key': 'cardImage', 'value': attachment['url']})

            keyworder.replace_texts(news_item.get('spinnedText'))

            post = WordPressPost()
            post.title = news_item.get('title')
            post.content = news_item.get('spinnedText')
            post.terms_names = {'post_tag': news_item.get(
                'keywords'), 'category': news_item.get('category')}
            post.post_status = 'publish'

            if attachment is not None:
                post.thumbnail = attachment['id']

            post.custom_fields = yoast

            post.id = self.client.call(NewPost(post))
            news_item['postId'] = post.id
            db().update_request_item(news_item)
            remove_images()

            return True
        except Exception as e:
            print(e)
            return False

    def upload_media(self, path, file_name, title, desc, mimetype):
        try:
            today = date.today()

            data = {
                'name': ' '.join(file_name.split()[:3]) + " " + today.strftime("%d%m%Y"),
                'type': mimetype,  # mimetype
                # 'caption': title,
                # 'description': desc,
                # 'struct': {'parent': 18271, 'title':'title'}
            }

            with open(path, 'rb') as img:
                data['bits'] = xmlrpc_client.Binary(img.read())

            uploaded = self.client.call(UploadFile(data))
            time.sleep(10)
            return uploaded
        except Exception as e:
            return None
