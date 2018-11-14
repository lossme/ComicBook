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

    @classmethod
    def send_request(cls, url, **kwargs):
        kwargs.setdefault('headers', cls.HEADERS)
        kwargs.setdefault('timeout', cls.TIMEOUT)
        return cls.session.get(url, **kwargs)

    @classmethod
    def get_html(cls, url):
        response = cls.send_request(url)
        return response.text

    @classmethod
    def create_comicbook(cls, comicid):
        url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(comicid)
        html = cls.get_html(url)

        name = cls.COMIC_NAME_PATTERN.search(html).group(1).strip()
        desc = cls.COMIC_DESC_PATTERN.search(html).group(1).strip()

        comicbook = ComicBook(name=name, desc=desc, tag=None, source_name=cls.source_name)
        comicbook._html = html
        comicbook._all_chapter = cls._get_all_chapter(comicid)
        max_chapter_number = len(comicbook._all_chapter)
        comicbook.get_max_chapter_number = lambda: max_chapter_number
        comicbook.get_chapter = functools.partial(cls.get_chapter, comicbook=comicbook)
        return comicbook

    @classmethod
    def get_chapter(cls, chapter_number, comicbook):
        max_chapter_number = int(comicbook.get_max_chapter_number())
        if int(chapter_number) < 0:
            chapter_number = max_chapter_number + chapter_number + 1
        try:
            chapter_title, chapter_number, chapter_url = comicbook._all_chapter[chapter_number]
            chapter = Chapter(title=chapter_title, chapter_number=chapter_number)
            chapter.get_chapter_images = functools.partial(cls.get_chapter_images,
                                                           url=chapter_url,
                                                           comicbook=comicbook)
            return chapter
        except KeyError:
            raise Exception("没找到资源 {} {}".format(comicbook.name, chapter_number))

    @classmethod
    def get_chapter_images(cls, url, comicbook):
        """根据章节的URL获取该章节的图片列表
        :param str url:  章节的URL如 http://ac.qq.com/ComicView/index/id/505430/cid/884
        :yield str pic_url: 漫画大图链接
        """
        html = cls.get_html(url)
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

    @classmethod
    def _get_all_chapter(cls, comicid):
        """根据漫画id获取所有的章节列表: http://ac.qq.com/Comic/ComicInfo/id/505430
        :param str/int comicid: 漫画id，如: 505430
        :param str name: 漫画名
        :return all_chapter: all_chapter = [(comic_title, chapter_title, chapter_number, chapter_url), ]
        """
        url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(comicid)
        html = cls.get_html(url)
        ol = re.search(r'(<ol class="chapter-page-all works-chapter-list".+?</ol>)', html, re.S).group()
        all_atag = re.findall(r'''<a.*?title="(.*?)".*?href="(.*?)">(.*?)</a>''', ol, re.S)
        all_chapter = {}
        for idx, item in enumerate(all_atag, start=1):
            try:
                # title = "航海王：第843话 温思默克·山智""
                # title = "秦侠：111.剥皮白王""
                # title = "爱情漫过流星：她在上面"
                title, url, _title = item
                p1 = re.search(r"""(?P<comic_title>.*?)：第(?P<chapter_number>\d+)话 (?P<chapter_title>.*?)""")
                p2 = re.search(r"""(?P<comic_title>.*?)：(?P<chapter_number>\d+)\.(?P<chapter_title>.*?)""")
                result = p1 or p2
                if result:
                    chapter_number = result.group('chapter_number')
                    chapter_title = result.group('chapter_title')
                else:
                    p3 = re.search(r"""(?P<comic_title>.*?)：(?P<chapter_title>.*?)""")
                    if p3:
                        chapter_title = p3.group('chapter_title')
                        chapter_number = idx

                chapter_url = parse.urljoin(cls.QQ_COMIC_HOST, url)
                all_chapter[chapter_number] = (chapter_title, chapter_number, chapter_url)
            except Exception:
                pass
        return all_chapter

    def search(self, name):
        url = "http://ac.qq.com/Comic/searchList/search/name"
        html = self.get_html(url)
        r = re.search(r'<ul class="mod_book_list mod_all_works_list mod_of">(.*?)</ul>', html, re.S)
        ul = r.group()

        r = re.findall(r'<h4 class="mod_book_name"><a href="(.*?)" title="(.*?)".*?</a></h4>', ul, re.S)
        for item in r:
            url, title = item
            comicid = url.rsplit('/')[-1]
            s = difflib.SequenceMatcher(None, title, name)
            if s.ratio() >= 0.5:
                return comicid
