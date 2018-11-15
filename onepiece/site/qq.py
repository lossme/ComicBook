import re
import base64
import json
import difflib
import functools
import warnings
from urllib import parse

import requests

from ..comicbook import ComicBook, Chapter, ImageInfo


class ComicBookCrawler:

    QQ_COMIC_HOST = 'http://ac.qq.com'
    HEADERS = {
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/65.0.3325.146 Safari/537.36')
    }
    TIMEOUT = 30
    source_name = '腾讯漫画'
    session = requests.session()

    COMIC_NAME_PATTERN = re.compile(r"""<h2 class="works-intro-title ui-left"><strong>(.*?)</strong></h2>""")
    COMIC_DESC_PATTERN = re.compile(r"""<p class="works-intro-short ui-text-gray9">(.*?)</p>""", re.S)

    CHAPTER_TITLE_PATTERN = re.compile(r"""<span class="title-comicHeading">(.*?)</span>""")

    def __init__(self, comicid):
        self.comicid = comicid

        self.comicbook_page_html = None

        # {int_chapter_number: chapter_page_html}
        self.chapter_page_html_db = {}

        # {int_chapter_number: chapter_page_url}
        self.chapter_page_url_db = {}

    @classmethod
    def create_comicbook(cls, comicid):
        crawler = cls(comicid=comicid)
        return ComicBook(comicbook_crawler=crawler)

    @classmethod
    def send_request(cls, url, **kwargs):
        kwargs.setdefault('headers', cls.HEADERS)
        kwargs.setdefault('timeout', cls.TIMEOUT)
        return cls.session.get(url, **kwargs)

    @classmethod
    def get_html(cls, url):
        response = cls.send_request(url)
        return response.text

    def get_comicbook_page_html(self):
        # http://ac.qq.com/Comic/ComicInfo/id/505430
        if not self.comicbook_page_html:
            url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(self.comicid)
            self.comicbook_page_html = self.get_html(url)
        return self.comicbook_page_html

    def get_chapter_page_url_db(self):
        if self.chapter_page_url_db:
            return self.chapter_page_url_db

        html = self.get_comicbook_page_html()
        ol = re.search(r'(<ol class="chapter-page-all works-chapter-list".+?</ol>)', html, re.S).group()
        all_atag = re.findall(r'''<a.*?title="(.*?)".*?href="(.*?)">(.*?)</a>''', ol, re.S)
        for idx, item in enumerate(all_atag, start=1):
            # title = "航海王：第916 和之国大相扑"         # p1
            # title = "航海王：第843话 温思默克·山智""     # p1
            # title = "秦侠：111.剥皮白王""                # p2
            # title = "爱情漫过流星：她在上面"             # 其他
            title, url, _title = item
            p1 = re.search(r"""(?P<comic_title>.*?)：第(?P<chapter_number>\d+)话? (?P<chapter_title>.*?)""", title)
            p2 = re.search(r"""(?P<comic_title>.*?)：(?P<chapter_number>\d+)\.(?P<chapter_title>.*?)""", title)
            if p1:
                chapter_number = p1.group('chapter_number')
            elif p2:
                chapter_number = p2.group('chapter_number')
            else:
                if chapter_number in self.chapter_page_url_db:
                    continue
                chapter_number = idx
            chapter_url = parse.urljoin(self.QQ_COMIC_HOST, url)
            chapter_number = int(chapter_number)
            self.chapter_page_url_db[chapter_number] = chapter_url
        return self.chapter_page_url_db

    def get_chapter_page_html(self, chapter_number):
        # http://ac.qq.com/ComicView/index/id/505430/cid/884
        if chapter_number not in self.chapter_page_html_db:
            chapter_page_url_db = self.get_chapter_page_url_db()
            if chapter_number not in chapter_page_url_db:
                raise Exception("没找到资源 {} {}".format(self.get_comicbook_name(), chapter_number))
            chapter_page_url = chapter_page_url_db[chapter_number]
            chapter_page_html = self.get_html(chapter_page_url)
            self.chapter_page_html_db[chapter_number] = chapter_page_html
        return self.chapter_page_html_db[chapter_number]

    def get_comicbook_name(self):
        html = self.get_comicbook_page_html()
        name = self.COMIC_NAME_PATTERN.search(html).group(1).strip()
        return name

    def get_comicbook_desc(self):
        html = self.get_comicbook_page_html()
        desc = self.COMIC_DESC_PATTERN.search(html).group(1).strip()
        return desc

    def get_comicbook_tag(self):
        return ""

    def get_max_chapter_number(self):
        return max(self.get_chapter_page_url_db().keys())

    def get_chapter_title(self, chapter_number):
        chapter_page_html = self.get_chapter_page_html(chapter_number)
        title = self.CHAPTER_TITLE_PATTERN.search(chapter_page_html).group(1)
        # title = "第843话 温思默克·山智""
        # title = "111.剥皮白王""
        # title = "爱情漫过流星：她在上面"
        p1 = re.search(r"""^第(?P<chapter_number>\d+)话? (?P<chapter_title>.*?)$""", title)
        p2 = re.search(r"""^(?P<chapter_number>\d+)\.(?P<chapter_title>.*?)$""", title)
        p3 = re.search(r"""^(?P<comic_title>.*?)：(?P<chapter_title>.*?)$""", title)
        if p1:
            chapter_title = p1.group('chapter_title')
        elif p2:
            chapter_title = p1.group('chapter_title')
        elif p3:
            chapter_title = p3.group('chapter_title')
        else:
            chapter_title = title
        return chapter_title

    def get_chapter_images(self, chapter_number):
        html = self.get_chapter_page_html(chapter_number)

        bs64_data = re.search(r"var DATA\s*=\s*'(.*?)'", html).group(1)
        json_str = ""
        for i in range(len(bs64_data)):
            try:
                s = base64.b64decode(bs64_data[i:]).decode('utf-8')
                json_str = "{" + re.search(r'("picture":.*)', s).group(1)
                break
            except Exception:
                pass
        datail_list = json.loads(json_str)['picture']
        images = [ImageInfo(item['url']) for item in datail_list]
        return images
