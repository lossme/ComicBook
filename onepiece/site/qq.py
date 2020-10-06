import re
import base64
import json
from urllib.parse import urljoin

from ..crawlerbase import (
    CrawlerBase,
    ChapterItem,
    ComicBookItem,
    Citem,
    SearchResultItem
)
from ..exceptions import ComicbookNotFound


class QQCrawler(CrawlerBase):

    SITE = "qq"
    SITE_INDEX = 'https://ac.qq.com/'
    LOGIN_URL = SITE_INDEX

    SOURCE_NAME = '腾讯漫画'

    COMIC_NAME_PATTERN = re.compile(r"""<h2 class="works-intro-title ui-left"><strong>(.*?)</strong></h2>""")
    COMIC_DESC_PATTERN = re.compile(r"""<p class="works-intro-short ui-text-gray9">(.*?)</p>""", re.S)

    CHAPTER_TITLE_PATTERN = re.compile(r"""<span class="title-comicHeading">(.*?)</span>""")

    SEARCH_NOT_FOUNT_PATTERN = re.compile(r'<div class="mod_960wr mod_of search_wr" style="background-color: #fff;">')
    SEARCH_UL_PATTERN = re.compile(r'<ul class="mod_book_list mod_all_works_list mod_of">(.*?)</ul>', re.S)
    SEARCH_LI_PATTERN = re.compile(r'<li>(.*?)</li>', re.S)
    SEARCH_DATA_PATTERN = re.compile("""<a href="/Comic/comicInfo/id/(?P<comicid>.*?)" \
title="(?P<name>.*?)" class="mod_book_cover db" \
target="_blank">.*?data-original=\'(?P<cover_image_url>.*?)\'""", re.S)

    TAG_PATTERN = re.compile(r"""<meta.*?的标签：(.*?)\"""", re.S)
    COVER_IMAGE_URL_PATTERN = re.compile(r'<div class="works-cover ui-left">.*?<img src="(.*?)"', re.S)
    AUTHOR_PATTERN = re.compile(r'<span class="first".*?作者：<em style="max-width: 168px;">(.*?)&nbsp')

    CHAPTER_JSON_STR_PATTERN = re.compile(r'("chapter":{.*)')
    DEFAULT_COMICID = 505430
    DEFAULT_COMIC_NAME = '海贼王'

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return 'https://ac.qq.com/Comic/ComicInfo/id/{}'.format(comicid)

    def get_index_page(self):
        if self.index_page is None:
            index_page = self.get_html(self.source_url)
            self.index_page = index_page
        return self.index_page

    def get_comicbook_item(self):
        # https://ac.qq.com/Comic/ComicInfo/id/505430
        html = self.get_html(self.source_url)
        r = self.COMIC_NAME_PATTERN.search(html)
        if not r:
            msg = ComicbookNotFound.TEMPLATE.format(site=self.SITE,
                                                    comicid=self.comicid,
                                                    source_url=self.source_url)
            raise ComicbookNotFound(msg)

        name = r.group(1).strip()
        desc = self.COMIC_DESC_PATTERN.search(html).group(1).strip()
        tag = self.TAG_PATTERN.search(html).group(1).strip()
        cover_image_url = self.COVER_IMAGE_URL_PATTERN.search(html).group(1)
        author = self.AUTHOR_PATTERN.search(html).group(1)

        citem_dict = {}
        ol = re.search(r'(<ol class="chapter-page-all works-chapter-list".+?</ol>)', html, re.S).group()
        all_atag = re.findall(r'''<a.*?title="(.*?)".*?href="(.*?)">(.*?)</a>''', ol, re.S)
        for idx, item in enumerate(all_atag, start=1):
            title, url, _title = item
            chapter_number = idx
            if chapter_number in citem_dict:
                continue

            chapter_page_url = urljoin(self.SITE_INDEX, url)

            citem_dict[chapter_number] = Citem(
                chapter_number=chapter_number,
                title=title,
                source_url=chapter_page_url)
        comicbook_item = ComicBookItem(name=name,
                                       desc=desc,
                                       tag=tag,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url,
                                       source_name=self.SOURCE_NAME,
                                       citem_dict=citem_dict)
        return comicbook_item

    def get_chapter_item(self, citem):
        chapter_page_html = self.get_html(citem.source_url)
        chapter_item = self.parser_chapter_page(chapter_page_html, source_url=citem.source_url)
        return chapter_item

    @classmethod
    def parser_chapter_page(cls, chapter_page_html, source_url=None):
        # 该方法只能解出部分数据，会缺失前面的一部分json字符串
        bs64_data = re.search(r"var DATA\s*=\s*'(.*?)'", chapter_page_html).group(1)
        for i in range(len(bs64_data)):
            try:
                json_str_part = base64.b64decode(bs64_data[i:]).decode('utf-8')
                break
            except Exception:
                pass
        else:
            raise

        json_str = "{" + cls.CHAPTER_JSON_STR_PATTERN.search(json_str_part).group(1)
        data = json.loads(json_str)
        title = data["chapter"]["cTitle"]
        chapter_number = data["chapter"]["cSeq"]
        image_urls = [item['url'] for item in data["picture"]]
        return ChapterItem(chapter_number=chapter_number,
                           title=title,
                           image_urls=image_urls,
                           source_url=source_url)

    def search(self, name, page=1, size=None):
        url = "https://ac.qq.com/Comic/searchList/search/{}/page/{}"\
            .format(name, page)
        html = self.get_html(url)
        if self.SEARCH_NOT_FOUNT_PATTERN.search(html):
            return []
        rv = []
        ul_tag = self.SEARCH_UL_PATTERN.search(html).group(1)
        for li_tag in self.SEARCH_LI_PATTERN.findall(ul_tag):
            r = self.SEARCH_DATA_PATTERN.search(li_tag)
            comicid = r.group("comicid")
            name = r.group("name")
            cover_image_url = r.group("cover_image_url")
            source_url = self.get_source_url(comicid)
            search_result_item = SearchResultItem(site=self.SITE,
                                                  comicid=comicid,
                                                  name=name,
                                                  cover_image_url=cover_image_url,
                                                  source_url=source_url)
            rv.append(search_result_item)
        return rv

    def login(self):
        self.selenium_login(
            login_url=self.LOGIN_URL,
            check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("nav_userinfo_cookie", domain="ac.qq.com"):
            return True
