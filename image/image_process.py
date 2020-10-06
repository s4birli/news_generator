from image.optimization import image_optimize, isImage, isJPEG
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts
from word_press import WordPress
from news.scraper import get_image
from datetime import date
from PIL import Image
import os
import uuid
import mimetypes
import time
import pathlib


def upload_image(url, news_item):
    try:
        image_url = news_item['image_url']
        uuid_txt = str(uuid.uuid1()).replace("-", "").upper()

        # Download File
        img_data = get_image(news_item['image_url'])
        file_name = "{}.{}".format(
            uuid_txt, image_url.split('/')[-1].split('.')[1])
        file_path = "{}/{}".format(pathlib.Path().absolute(), file_name)
        with open(file_path, 'wb') as handler:
            handler.write(img_data.content)

        # convert image to jpg
        img_type = isJPEG(file_path)
        if img_type is False:
            im = Image.open(file_path)
            rgb_im = im.convert('RGB')
            file_path = "{}\\{}.{}".format(os.getcwd(), uuid_txt, "jpg")
            rgb_im.save(file_path)

        # Optimize
        image_optimize(file_path)

        # get minetype
        mimetype = get_mimetypes(file_name)
        if mimetype == "":
            mimetype = "image/jpeg"

        return WordPress.WordPress(url).upload_media(
            file_path, news_item['title'], news_item['title'], news_item['description'][:100], mimetype)
    except Exception as e:
        print(e)
        return None


def get_mimetypes(file_name):
    try:
        _res = mimetypes.read_mime_types(file_name)
        if _res is None:
            _res = mimetypes.guess_type(file_name)[0]

        return _res
    except:
        pass

    try:
        _res = mimetypes.guess_type(file_name)[0]
        return _res
    except:
        pass

    return None
