from news.scraper import get_response
from keyworder.cleaner import clean_title
from data.mongodb import db
from news import SimplyNews
from spin_rewriter import SpinRewriter
from keyworder.keyworder import add_internal_link
from word_press import WordPress
import time
import random


class News(object):
    def __init__(self, url, req):
        self.url = url
        self.request = req

    def scrab(self):
        items = get_response(
            self.request['url'], 'xml').findAll('item')[0:10]

        published_item = 0
        for item in items:
            if published_item > 4:
                break

            try:
                if "/transfer-centre" in item.link.text:
                    continue

                guid = item.guid.text if item.guid is not None else item.link.text
                news_item = {'guid': guid}

                title = clean_title(item.title.text)
                published = False

                if db().exist(news_item):
                    news_item['urlId'] = self.url.get('_id')
                    simplynews = SimplyNews(item.link.text, 'en')
                    simplynews.cleaned_news()
                    if simplynews.text is None:
                        continue

                    simplynews.published_date = item.pubDate.text if simplynews.published_date is None else simplynews.published_date

                    spinrewritter = SpinRewriter()
                    format_text = {
                        'title': title, 'text': simplynews.text, 'desc': simplynews.desc}
                    text = "{title} || {text} || {desc}".format(**format_text)
                    spinnedtext = spinrewritter.unique_variation(text)

                    if spinnedtext is None:
                        print('full_context is None')
                        continue

                    spinnedtextarray = spinnedtext.split("||")
                    title = spinnedtextarray[0].strip()
                    simplynews.text = spinnedtextarray[1].strip()
                    simplynews.desc = spinnedtextarray[2].strip()

                    simplynews.keywords.append("Hot News")
                    simplynews.text = simplynews.corrected_sub_tag(
                        simplynews.text)
                    # desc = article.meta_description if len(article.meta_description) > 0 else article.text[:150]
                    news_item['attachmentId'] = ''
                    news_item['postId'] = ''
                    news_item['title'] = title
                    news_item['pubdate'] = item.pubDate.text
                    news_item['requestsId'] = self.request.get('_id')
                    news_item['category'] = self.request.get('category')
                    news_item['image_url'] = simplynews.top_image_url.replace(
                        "/branded_news/", "/cpsprodpb/")
                    news_item['description'] = simplynews.desc
                    news_item['isPublished'] = False
                    news_item['keywords'] = simplynews.keywords
                    news_item['spinnedText'] = add_internal_link(
                        self.url, self.request, simplynews.text)

                    _news_item = db().add_request_items(news_item)
                    published = WordPress.WordPress(
                        self.url).publish_article(news_item)
                else:
                    news_item = db().find_request(news_item)
                    if news_item["isPublished"] is False:
                        published = WordPress.WordPress(
                            self.url).publish_article(news_item)

                if published is True:
                    db().request_update(news_item)
                    time.sleep(30)

                    WordPress.WordPress(self.url).update_post(news_item)

                    published_item += 1

                    r = random.randrange(63, 113)
                    time.sleep(r)

            except Exception as e:
                print(e)
