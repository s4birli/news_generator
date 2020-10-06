from news import ArticleScraper
import requests


class SimplyNews(object):
    """A facade for easier usage of the newspaper repo."""

    def __init__(self, url, language):
        """Return unique variation of the given text.
        :param url: url to request
        :type text: string
        :param language: language to request
        :type text: string ['en', 'tr']
        """
        self.url = url
        self.language = language
        self.text = ''
        self.original_text = ''
        self.original_html = ''
        self.keywords = []
        self.desc = ''
        self.title = ''
        self.top_image_url = ''
        self.images = []
        self.published_date = None
        self.authors = []

    def raw_news(self):
        """resolves raw scrubed news

        :return: items
        self.text = ''
        self.original_text = ''
        self.original_html = ''
        self.keywords = []
        self.desc = ''
        self.title = ''
        self.top_image_url = ''
        self.images = []
        self.published_date = None
        self.authors = []
        """
        article = ArticleScraper.get_article(self.url, self.language)

        self.original_text = article.text
        self.original_html = article.article_html
        self.keywords = article.keywords
        self.desc = article.summary
        self.title = article.title
        self.top_image_url = article.top_img
        self.images = article.imgs
        self.published_date = article.publish_date
        self.authors = article.authors
        self.text = article.text

    def cleaned_news(self, sub_title_char=['[', ']']):
        """resolves cleaned scrubed news
        removed images and titles of the image
        remove emails from the news
        default change h2, h3, h4 tags with [h2], [h3], [h4]

        :params sub_title_char example: ['[', ']']
        :type array: array
        :return: items
        self.text = ''
        self.original_text = ''
        self.original_html = ''
        self.keywords = []
        self.desc = ''
        self.title = ''
        self.top_image_url = ''
        self.images = []
        self.published_date = None
        self.authors = []
        """
        article = ArticleScraper.get_article(self.url, self.language)

        self.original_text = article.text
        self.original_html = article.article_html
        self.keywords = article.keywords
        self.desc = article.summary
        self.title = article.title
        self.top_image_url = article.top_img
        self.images = article.imgs
        self.published_date = article.publish_date
        self.authors = article.authors
        self.text = ArticleScraper.reformat_text(
            self.url, False)

    def prettier_news(self):
        """resolves cleaned scrubed news
        removed images and titles of the image
        remove emails from the news
        add h2, h3, h4 tags to text

        :return: items
        self.text = ''
        self.original_text = ''
        self.original_html = ''
        self.keywords = []
        self.desc = ''
        self.title = ''
        self.top_image_url = ''
        self.images = []
        self.published_date = None
        self.authors = []
        """
        article = ArticleScraper.get_article(self.url, self.language)

        self.original_text = article.text
        self.original_html = article.article_html
        self.keywords = article.keywords
        self.desc = article.summary
        self.title = article.title
        self.top_image_url = article.top_img
        self.images = article.imgs
        self.published_date = article.publish_date
        self.authors = article.authors
        self.text = ArticleScraper.reformat_text(self.url, True)

    def corrected_sub_tag(self, text):
        return ArticleScraper.corrected_sub_tag(text)
