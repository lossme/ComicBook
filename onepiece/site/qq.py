import re
import base64
import json
import difflib
from urllib import parse

import requests

from . import Chapter


class ComicBook:

    QQ_COMIC_HOST = 'http://ac.qq.com'
    HEADERS = {
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/65.0.3325.146 Safari/537.36')
    }
    TIMEOUT = 30

    def __init__(self):
        self.session = requests.session()
        self.name = '腾讯漫画'

    def send_request(self, url, **kwargs):
        kwargs.setdefault('headers', self.HEADERS)
        kwargs.setdefault('timeout', self.TIMEOUT)
        return self.session.get(url, **kwargs)

    def get_html(self, url):
        response = self.send_request(url)
        return response.text

    def get_all_chapter(self, comicid=None, name=None):
        """根据漫画id获取所有的章节列表: http://ac.qq.com/Comic/ComicInfo/id/505430
        :param str/int comicid: 漫画id，如: 505430
        :param str name: 漫画名
        :return all_chapter: all_chapter = [(comic_title, chapter_title, chapter_number, chapter_url), ]
        """
        if not comicid:
            comicid = self.search(name)
        url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(comicid)
        html = self.get_html(url)
        ol = re.search(r'(<ol class="chapter-page-all works-chapter-list".+?</ol>)', html, re.S).group()
        all_atag = re.findall(r'''<a.*?title="(.*?)".*?href="(.*?)">(.*?)</a>''', ol, re.S)
        all_chapter = {}
        for item in all_atag:
            # title = '航海王：第843话 温思默克·山智'
            title, url, _title = item
            r1 = title.split('：', 1)
            comic_title = r1[0]
            s = r1[-1]
            r2 = s.split(' ', 1)
            chapter_number = int(re.search(r'\d+', r2[0]).group())
            chapter_title = r2[-1]
            chapter_url = parse.urljoin(self.QQ_COMIC_HOST, url)
            all_chapter[chapter_number] = (comic_title, chapter_title, chapter_number, chapter_url)
        return all_chapter

    def get_chapter_pics(self, url):
        """根据章节的URL获取该章节的图片列表
        :param str url:  章节的URL如 http://ac.qq.com/ComicView/index/id/505430/cid/884
        :yield str pic_url: 漫画大图链接
        """
        html = self.get_html(url)
        bs64_data = re.search(r"var DATA.+?= '(.+)'", html).group(1)[1:]
        json_str = base64.b64decode(bs64_data).decode('utf-8')
        datail_list = json.loads(json_str)['picture']
        for i in datail_list:
            yield i['url']

    def get_task_chapter(self, comicid=None, name=None, chapter_number_list=None, is_download_all=None):
        """根据参数来确定下载哪些章节
        :param str/int comicid: 漫画id
        :param list chapter_number_list: 需要下载的章节列表，如 chapter_number_list = [1, 2, 3]
        :param boolean is_download_all: 若设置成True，则下载该漫画的所有章节
        :yield chapter: Chapter instance
        """
        all_chapter = self.get_all_chapter(comicid, name)
        max_chapter_number = max(all_chapter.keys())
        if is_download_all:
            return list(all_chapter.values())

        for idx in chapter_number_list:
            chapter_number = idx if idx >= 0 else max_chapter_number + idx + 1
            value = all_chapter.get(chapter_number)
            if value is None:
                print('找不到第{}集资源'.format(chapter_number))
                continue
            comic_title, chapter_title, chapter_number, chapter_url = value
            chapter = Chapter(chapter_number=chapter_number,
                              chapter_title=chapter_title,
                              comic_title=comic_title,
                              chapter_pics=self.get_chapter_pics(chapter_url),
                              site_name=self.name
                              )
            yield chapter

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
