import re
import collections
import json
import base64
import urllib.parse

from . import ComicBookCrawlerBase, ChapterItem, ComicBookItem, SearchResultItem
from ..exceptions import ChapterNotFound, ComicbookNotFound


class ComicBookCrawler(ComicBookCrawlerBase):

    SOURCE_NAME = "有妖气"
    SITE = "u17"

    CItem = collections.namedtuple("CItem", ["chapter_number", "title", "url", "chapter_id"])
    COMIC_NAME_PATTERN = re.compile(r'<h1 class="fl".*?>(.*?)</h1>', re.S)
    DESC_ALL_PATTERN = re.compile(r'<div class="textbox" id="words_all".*?>.*?<p class="ti2">(.*?)</p>', re.S)
    DESC_PATTERN = re.compile(r'<p class="words" id="words">(.*?)<', re.S)

    UL_PATTERN = re.compile(r'<ul class="cf" id="chapter">(.*?)</ul>', re.S)
    LI_DATA_PATTERN = re.compile(
        r'<li.*?>\s*<a.*?href="(?P<url>.*?)"\s*title="(?P<title>.*?)".*?</li>', re.S)
    TAG_HTLM_PATTERN = re.compile(r'<div class="line1">(.*?)</div>', re.S)
    TAG_PATTERN = re.compile(r'<a .*?>\s*(.*?)\s*</a>', re.S)
    COVER_IMAGE_URL_PATTERN = re.compile(r'var cover_url = "(.*?)";')
    AUTHOR_PATTERN = re.compile(r'<div class="author_info">.*?<a.*?class="name">(.*?)</a>', re.S)
    IMAGE_CONFIG_PATTERN = re.compile(r'var image_config = (\{.*?\});', re.S)
    IMAGE_CONFIG_KEY_PATTERN = re.compile(r'\s*(.\w+): ')

    SEARCH_UL_PATTERN = re.compile(r'<div class="comiclist">\s*<ul>(.*?)</ul>', re.S)
    SEARCH_LI_TAG_PATTERN = re.compile(r'<li>(.*?)</li>', re.S)
    SEARCH_DATA_PATTERN = re.compile(
        r'<strong><a href="https?://www.u17.com/comic/(\d+).html" target="_blank" class="u" title="(.*?)">')
    SEARCH_COVER_IMAGE_URL_PATTERN = re.compile(r'<div class="cover">.*?<img src="(.*?)">')
    COMIC_BOOK_API = "https://www.u17.com/comic/ajax.php?mod=chapter&act=get_chapter_list&comic_id={comicid}"
    CHAPTER_API = "https://www.u17.com/comic/ajax.php?mod=chapter&act=get_chapter_v5&chapter_id={chapter_id}"
    CHAPTER_URL = "https://www.u17.com/chapter/{chapter_id}.html"

    def __init__(self, comicid):
        super().__init__()
        self.comicid = comicid
        self.source_url = "http://www.u17.com/comic/{}.html".format(comicid)

        # {int_chapter_number: CItem}
        self.chapter_db = {}

        self.index_page = None
        self.api_data = None

    def get_api_data(self):
        if self.api_data is None:
            url = self.COMIC_BOOK_API.format(comicid=self.comicid)
            self.api_data = self.get_json(url)
        return self.api_data

    def get_index_page(self):
        if self.index_page is None:
            response = self.send_request("GET", self.source_url)
            self.index_page = response.text
        return self.index_page

    def get_chapter_db(self):
        if self.chapter_db:
            return self.chapter_db
        api_data = self.get_api_data()
        for idx, item in enumerate(api_data['chapter_list'], start=1):
            chapter_id = item['chapter_id']
            title = item['name']
            chapter_url = self.CHAPTER_URL.format(chapter_id=chapter_id)
            self.chapter_db[idx] = self.CItem(
                chapter_number=idx,
                url=chapter_url,
                title=title,
                chapter_id=chapter_id)
        return self.chapter_db

    def get_comicbook_item(self):
        html = self.get_index_page()
        try:
            name = self.COMIC_NAME_PATTERN.search(html).group(1)
            name = name.strip()
        except Exception:
            msg = ComicbookNotFound.TEMPLATE.format(site=self.SITE,
                                                    comicid=self.comicid,
                                                    source_url=self.source_url)
            raise ComicbookNotFound(msg)

        r = self.DESC_ALL_PATTERN.search(html)
        if r:
            desc = r.group(1)
        else:
            desc = self.DESC_PATTERN.search(html).group(1)

        cover_image_url = self.COVER_IMAGE_URL_PATTERN.search(html).group(1)
        author = self.AUTHOR_PATTERN.search(html).group(1)
        tag_html = self.TAG_HTLM_PATTERN.search(html).group(1)
        tag = ','.join(self.TAG_PATTERN.findall(tag_html)[:-1])

        chapter_db = self.get_chapter_db()

        chapters = []
        for chapter_number, item in chapter_db.items():
            chapter = ComicBookItem.create_chapter(chapter_number=chapter_number, title=item.title)
            chapters.append(chapter)

        return ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             cover_image_url=cover_image_url,
                             author=author,
                             source_url=self.source_url,
                             source_name=self.SOURCE_NAME,
                             chapters=chapters)

    def get_chapter_item(self, chapter_number):
        chapter_db = self.get_chapter_db()
        if chapter_number not in chapter_db:
            msg = ChapterNotFound.TEMPLATE.format(site=self.SITE,
                                                  comicid=self.comicid,
                                                  chapter_number=chapter_number,
                                                  source_url=self.source_url)
            raise ChapterNotFound(msg)

        chapter_id = chapter_db[chapter_number].chapter_id
        chapter_url = chapter_db[chapter_number].url
        chapter_api_url = self.CHAPTER_API.format(chapter_id=chapter_id)
        data = self.get_json(chapter_api_url)
        title = data["chapter"]["name"]
        image_urls = []
        for item in data["image_list"]:
            # image_url = base64.b64decode(v["lightning"].encode()).decode()
            image_urls.append(item['src'])
        return ChapterItem(chapter_number=chapter_number, title=title, image_urls=image_urls, source_url=chapter_url)

    @classmethod
    def search(cls, name):
        url = "http://so.u17.com/all/{}/m0_p1.html".format(urllib.parse.quote(name))
        html = cls.get_html(url)
        ul_tag = cls.SEARCH_UL_PATTERN.search(html).group(1)
        rv = []
        for li_tag in cls.SEARCH_LI_TAG_PATTERN.findall(ul_tag):
            cover_image_url = cls.SEARCH_COVER_IMAGE_URL_PATTERN.search(li_tag).group(1)
            comicid, name = cls.SEARCH_DATA_PATTERN.search(li_tag).groups()
            source_url = "http://www.u17.com/comic/{}.html".format(comicid)

            item = SearchResultItem(site=cls.SITE,
                                    comicid=comicid,
                                    name=name,
                                    cover_image_url=cover_image_url,
                                    source_url=source_url)
            rv.append(item)
        return rv

    @classmethod
    def login(cls):
        login_url = "http://passport.u17.com/member_v2/login.php?url=http://www.u17.com/"
        cls.selenium_login(login_url=login_url, check_login_status_func=cls.check_login_status)

    @classmethod
    def check_login_status(cls):
        session = cls.get_session()
        if session.cookies.get("xxauthkey", domain=".u17.com"):
            return True
