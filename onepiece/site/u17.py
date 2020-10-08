import re
import urllib.parse

from ..crawlerbase import (
    CrawlerBase,
    ChapterItem,
    ComicBookItem,
    Citem,
    SearchResultItem
)
from ..exceptions import ComicbookNotFound


class U17Crawler(CrawlerBase):

    SOURCE_NAME = "有妖气"
    SITE = "u17"
    SITE_INDEX = 'https://www.u17.com/'

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
    LOGIN_URL = "https://passport.u17.com/member_v2/login.php?url=https://www.u17.com/"

    DEFAULT_COMICID = 195
    DEFAULT_SEARCH_NAME = '雏蜂'

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return "https://www.u17.com/comic/{}.html".format(comicid)

    def get_comicbook_item(self):
        response = self.send_request("GET", self.source_url)
        html = response.text
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

        citem_dict = {}
        url = self.COMIC_BOOK_API.format(comicid=self.comicid)
        api_data = self.get_json(url)
        for idx, item in enumerate(api_data['chapter_list'], start=1):
            chapter_number = idx
            chapter_id = item['chapter_id']
            title = item['name']
            chapter_url = self.CHAPTER_URL.format(chapter_id=chapter_id)
            citem_dict[chapter_number] = Citem(
                chapter_number=chapter_number,
                title=title,
                source_url=chapter_url,
                chapter_id=chapter_id)
        return ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             cover_image_url=cover_image_url,
                             author=author,
                             source_url=self.source_url,
                             source_name=self.SOURCE_NAME,
                             citem_dict=citem_dict)

    def get_chapter_item(self, citem):
        chapter_id = citem.chapter_id
        chapter_api_url = self.CHAPTER_API.format(chapter_id=chapter_id)
        data = self.get_json(chapter_api_url)
        title = data["chapter"]["name"]
        image_urls = []
        for item in data["image_list"]:
            image_urls.append(item['src'])
        return ChapterItem(chapter_number=citem.chapter_number,
                           title=title,
                           image_urls=image_urls,
                           source_url=citem.source_url)

    def search(self, name, page=1, size=None):
        url = "http://so.u17.com/all/{}/m0_p{}.html"\
            .format(urllib.parse.quote(name), page)
        html = self.get_html(url)
        ul_tag = self.SEARCH_UL_PATTERN.search(html).group(1)
        rv = []
        for li_tag in self.SEARCH_LI_TAG_PATTERN.findall(ul_tag):
            cover_image_url = self.SEARCH_COVER_IMAGE_URL_PATTERN.search(li_tag).group(1)
            comicid, name = self.SEARCH_DATA_PATTERN.search(li_tag).groups()
            source_url = self.get_source_url(comicid)
            item = SearchResultItem(site=self.SITE,
                                    comicid=comicid,
                                    name=name,
                                    cover_image_url=cover_image_url,
                                    source_url=source_url)
            rv.append(item)
        return rv

    def login(self):
        self.selenium_login(
            login_url=self.LOGIN_URL, check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("xxauthkey", domain=".u17.com"):
            return True
