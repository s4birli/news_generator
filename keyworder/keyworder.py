from word_press import WordPress
from data.mongodb import db
import collections
import re
import ssl


def get_post(url, request):
    try:
        wordpress = WordPress.WordPress(url)
        return wordpress.get_latest_post_by_category(request.get('category'))
    except Exception as e:
        return None


def get_combination(text):
    try:
        get_forbidden_url_words = db().get_forbidden_url_words()

        for forbidden in get_forbidden_url_words:
            text = re.sub(forbidden["value"], "", text, 5000000)

        lines = re.split("\n", text)
        combinations = []

        for line in lines:
            x = re.split(" ", line.strip())
            words = []
            for i in range(len(x)):
                if len(x[i].strip()) > 3 and {"value": x[i].strip()} not in get_forbidden_url_words:
                    words.append(x[i])
                else:
                    continue

            for i in range(len(words) - 1):
                if len(words[i].strip()) > 0:
                    combinations.append(words[i] + " " + words[i + 1])

        Counter = collections.Counter(combinations)
        return Counter.most_common(len(combinations))
    except Exception as e:
        print(e)
        return None


def get_mostCommon(text1, text2):
    list1 = get_combination(text1)
    list2 = get_combination(text2)
    return_item = ""
    for first in list1:
        for second in list2:
            if first[0] == second[0]:
                return_item = first[0]
                break
    if len(return_item) == 0:
        return_item = list2[0][0]

    return return_item


def add_internal_link(url, request, text, title):
    try:
        previous_post = get_post(url, request)
        title = previous_post.title if previous_post else title
        search_text = get_mostCommon(title, text)
        original_text = text

        if previous_post:
            replace_text = '<a href="{}" target="_self">{}</a>'.format(previous_post.link, search_text)
            return re.sub(search_text, replace_text, original_text, 1)
        else:
            return original_text
            
    except Exception as e:
        print(e)
        return None


def get_focus(title, tags):
    focus = ""
    try:
        for tag in tags:
            for title in title.split(' '):
                if tag == title:
                    focus = focus + " " + tag
    except Exception as e:
        print(e)

    return focus


def replace_texts(text):
    get_forbidden_words = db().get_forbidden_words()
    for word in get_forbidden_words:
        text = text.replace(word['value'], "")
    return text
