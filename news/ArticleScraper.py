from newspaper import Article, fulltext
from bs4 import BeautifulSoup
import requests
import re


def get_article(url, language='en'):
    try:
        _url = url.strip()
        article = Article(_url, language=language)
        article.download()
        article.parse()

        try:
            article.nlp()
        except Exception as e:
            print(e)
            pass
        if article.summary is None or len(article.summary) is 0:
            article.summary = article.meta_description if len(
                article.meta_description) > 0 else article.text[:150]

        return article
    except Exception as e:
        raise Exception('')


def get_html(url):
    request_headers = {
        "Accept-Language": "en-US,en;q=0.5",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
        "Content-Type": "Text",
        "Connection": "keep-alive"
    }
    req = requests.get(url, headers=request_headers)
    return BeautifulSoup(req.content, features="html.parser")


def clean_email(text):
    return re.sub(r"\S*@\S*\s?", "", text, flags=re.MULTILINE)


def clean_twitter(text):
    return re.sub(r"Follow+.*@[A-Za-z0-9]+", "", text, flags=re.MULTILINE)


def clean_url(text):
    return re.sub(r"http\S+", "", text, flags=re.MULTILINE)


def remove_img_tags(data):
    p = re.compile(r'<img.*?/>')
    return p.sub('', data)


def remove_figure_tags(data):
    p = re.compile(r'<figure.*?/>')
    return p.sub('', data)


def reformat_text(link, sub_title=False):
    try:
        soup = get_html(link)
        try:
            for figure in soup.find_all('figure'):
                try:
                    figure.decompose()
                except:
                    pass

            for img in soup.find_all('img'):
                try:
                    img.decompose()
                except:
                    pass
        except Exception as e:
            print(e)
            pass

        text = fulltext(str(soup.currentTag))
        text = clean_twitter(text)
        text = clean_url(text)
        text = clean_email(text)
        text = add_sub_title_html(soup, text) if sub_title else add_sub_title(
            soup, text)
        return text
    except Exception as e:
        print(e)
        pass


def add_sub_title(soup, text):
    try:
        for i in ['2', '3', '4']:
            for sub in soup.find_all(['h' + i]):
                original_text = text
                search_text = sub.text
                replace_text = '[h{}]{}[/h{}]'.format(i, search_text, i,)
                sub_text = re.sub(search_text, replace_text, original_text, 1)
                text = sub_text
    except Exception as e:
        print(e)

    return text


def corrected_sub_tag(text):
    for i in ['2', '3', '4']:
        match_list = re.findall(r"^(\[h.+" + i + "+\])$", text, re.MULTILINE)
        for match in match_list:
            original_text = match
            replace_text = match.replace("[h" + i, "<h" + i)
            replace_text = replace_text.replace("[/h" + i, "</h" + i)
            replace_text = replace_text.replace("]", ">")
            text = text.replace(original_text, replace_text)

    return text


def add_sub_title_html(soup, text):
    try:
        for i in ['2', '3', '4']:
            for sub in soup.find_all(['h' + i]):
                original_text = text
                search_text = sub.text
                replace_text = '<h{}>{}</h{}>'.format(i, search_text, i)
                sub_text = re.sub(search_text, replace_text, original_text, 1)
                text = sub_text
    except Exception as e:
        print(e)

    return text
