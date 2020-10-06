import requests
from bs4 import BeautifulSoup

request_headers = {
    "Accept-Language": "en-US,en;q=0.5",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Content-Type": "Text",
    "Connection": "keep-alive"
}


def get_response(url, features):
    resp = requests.get(url, headers=request_headers)
    return BeautifulSoup(resp.content, features=features)


def get_image(url):
    return requests.get(url, headers=request_headers, stream=True)
