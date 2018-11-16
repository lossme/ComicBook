import re
import base64
import json
from urllib import parse


from . import ComicBookCrawlerBase
from ..exceptions import ChapterSourceNotFound


class ComicBookCrawler(ComicBookCrawlerBase):

    QQ_COMIC_HOST = 'http://ac.qq.com'

    source_name = '腾讯漫画'

    COMIC_NAME_PATTERN = re.compile(r"""<h2 class="works-intro-title ui-left"><strong>(.*?)</strong></h2>""")
    COMIC_DESC_PATTERN = re.compile(r"""<p class="works-intro-short ui-text-gray9">(.*?)</p>""", re.S)

    CHAPTER_TITLE_PATTERN = re.compile(r"""<span class="title-comicHeading">(.*?)</span>""")

    def __init__(self, comicid):
        super().__init__()

        self.comicid = comicid
        self.comicbook_page_html = None

        # {int_chapter_number: chapter_page_url}
        self.chapter_page_url_db = {}

        self.comicbook = None

        # {int_chapter_number: Chapter}
        self.chapter_db = {}

    def get_comicbook_page_html(self):
        if self.comicbook_page_html is None:
            url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(self.comicid)
            comicbook_page_html = self.get_html(url)
            self.comicbook_page_html = comicbook_page_html
        return self.comicbook_page_html

    def get_chapter_page_url_db(self):
        if self.chapter_page_url_db:
            return self.chapter_page_url_db
        html = self.get_comicbook_page_html()
        self.chapter_page_url_db = self.parser_chapter_url_from_comicbook_page(html)
        return self.chapter_page_url_db

    def get_comicbook(self):
        # http://ac.qq.com/Comic/ComicInfo/id/505430
        if self.comicbook:
            return self.comicbook
        html = self.get_comicbook_page_html()
        name = self.COMIC_NAME_PATTERN.search(html).group(1).strip()
        desc = self.COMIC_DESC_PATTERN.search(html).group(1).strip()
        tag = ""
        chapter_page_url_db = self.get_chapter_page_url_db()

        self.comicbook = self.ComicBook(name=name,
                                        desc=desc,
                                        tag=tag,
                                        max_chapter_number=max(chapter_page_url_db.keys())
                                        )
        return self.comicbook

    def get_chapter(self, chapter_number):
        if chapter_number in self.chapter_db:
            return self.chapter_db[chapter_number]

        chapter_page_url_db = self.get_chapter_page_url_db()
        if chapter_number not in chapter_page_url_db:
            raise ChapterSourceNotFound("没找到资源 {} {}".format(self.get_comicbook_name(), chapter_number))
        chapter_page_url = chapter_page_url_db[chapter_number]
        chapter_page_html = self.get_html(chapter_page_url)
        self.chapter_db[chapter_number] = self.parser_chapter_page(chapter_page_html)
        return self.chapter_db[chapter_number]

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

            chapter_url = parse.urljoin(cls.QQ_COMIC_HOST, url)
            chapter_number = int(chapter_number)
            chapter_page_url_db[chapter_number] = chapter_url
        return chapter_page_url_db

    @classmethod
    def parser_chapter_page(cls, chapter_page_html):
        title = cls.CHAPTER_TITLE_PATTERN.search(chapter_page_html).group(1)
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

        # image_urls
        bs64_data = re.search(r"var DATA\s*=\s*'(.*?)'", chapter_page_html).group(1)
        json_str = ""
        for i in range(len(bs64_data)):
            try:
                s = base64.b64decode(bs64_data[i:]).decode('utf-8')
                json_str = "{" + re.search(r'("picture":.*)', s).group(1)
                break
            except Exception:
                pass
        datail_list = json.loads(json_str)['picture']
        image_urls = [item['url'] for item in datail_list]
        return cls.Chapter(chapter_title=chapter_title, image_urls=image_urls)
