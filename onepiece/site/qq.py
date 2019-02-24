import re
import base64
import json
from urllib import parse

from . import (ComicBookCrawlerBase, ChapterItem, ComicBookItem, SearchResultItem,
               ChapterSourceNotFound, ComicbookNotFound)


class ComicBookCrawler(ComicBookCrawlerBase):

    QQ_COMIC_HOST = 'https://ac.qq.com'
    SITE = "qq"
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

    def __init__(self, comicid):
        super().__init__()
        self.comicid = comicid
        self.comicbook_page_html = None

        # {int_chapter_number: chapter_page_url}
        self._chapter_page_url_db = None

        self.source_url = 'https://ac.qq.com/Comic/ComicInfo/id/{}'.format(self.comicid)

    def get_comicbook_page_html(self):
        if self.comicbook_page_html is None:
            comicbook_page_html = self.get_html(self.source_url)
            self.comicbook_page_html = comicbook_page_html
        return self.comicbook_page_html

    def get_chapter_page_url(self, chapter_number):
        if chapter_number not in self.chapter_page_url_db:
            msg = "资源未找到！ site={} comicid={} chapter_number={}".format(self.SITE, self.comicid, chapter_number)
            raise ChapterSourceNotFound(msg)
        return self.chapter_page_url_db[chapter_number]

    @property
    def chapter_page_url_db(self):
        if self._chapter_page_url_db is None:
            html = self.get_comicbook_page_html()
            self._chapter_page_url_db = self.parser_chapter_url_from_comicbook_page(html)
        return self._chapter_page_url_db

    def get_comicbook_item(self):
        # https://ac.qq.com/Comic/ComicInfo/id/505430
        html = self.get_comicbook_page_html()
        name = self.COMIC_NAME_PATTERN.search(html).group(1).strip()
        desc = self.COMIC_DESC_PATTERN.search(html).group(1).strip()
        tag = self.TAG_PATTERN.search(html).group(1).strip()
        cover_image_url = self.COVER_IMAGE_URL_PATTERN.search(html).group(1)
        author = self.AUTHOR_PATTERN.search(html).group(1)

        max_chapter_number = max(self.chapter_page_url_db.keys())
        comicbook_item = ComicBookItem(name=name,
                                       desc=desc,
                                       tag=tag,
                                       max_chapter_number=max_chapter_number,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url,
                                       source_name=self.SOURCE_NAME)
        return comicbook_item

    def get_chapter_item(self, chapter_number):
        chapter_page_url = self.get_chapter_page_url(chapter_number)
        chapter_page_html = self.get_html(chapter_page_url)
        chapter_item = self.parser_chapter_page(chapter_page_html, source_url=chapter_page_url)
        return chapter_item

    @classmethod
    def parser_chapter_url_from_comicbook_page(cls, comicbook_page_html):
        chapter_page_url_db = {}
        ol = re.search(r'(<ol class="chapter-page-all works-chapter-list".+?</ol>)', comicbook_page_html, re.S).group()
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
                chapter_number = idx

            if chapter_number in chapter_page_url_db:
                continue

            chapter_page_url = parse.urljoin(cls.QQ_COMIC_HOST, url)
            chapter_number = int(chapter_number)
            chapter_page_url_db[chapter_number] = chapter_page_url
        return chapter_page_url_db

    @classmethod
    def parser_chapter_page(cls, chapter_page_html, source_url=None):
        # 该方法只能解出部分数据，会缺失前面的一部分json字符串
        bs64_data = re.search(r"var DATA\s*=\s*'(.*?)'", chapter_page_html).group(1)
        for i in range(len(bs64_data)):
            try:
                json_str_part = base64.b64decode(bs64_data[i:]).decode('utf-8')
                break
            except Exception as e:
                pass
        else:
            raise

        json_str = "{" + cls.CHAPTER_JSON_STR_PATTERN.search(json_str_part).group(1)
        data = json.loads(json_str)
        title = data["chapter"]["cTitle"]
        chapter_number = data["chapter"]["cSeq"]
        image_urls = [item['url'] for item in data["picture"]]
        return ChapterItem(chapter_number=chapter_number, title=title, image_urls=image_urls, source_url=source_url)

    @classmethod
    def search(cls, name):
        url = "https://ac.qq.com/Comic/searchList/search/{}".format(name)

        html = cls._get_html(url)
        if cls.SEARCH_NOT_FOUNT_PATTERN.search(html):
            return []
        rv = []
        ul_tag = cls.SEARCH_UL_PATTERN.search(html).group(1)
        for li_tag in cls.SEARCH_LI_PATTERN.findall(ul_tag):
            r = cls.SEARCH_DATA_PATTERN.search(li_tag)
            search_result_item = SearchResultItem(site=cls.SITE,
                                                  comicid=r.group("comicid"),
                                                  name=r.group("name"),
                                                  cover_image_url=r.group("cover_image_url"))
            rv.append(search_result_item)
        return rv
