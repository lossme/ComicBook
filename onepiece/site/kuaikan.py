import re

import execjs

import logging

from ..crawlerbase import (
    CrawlerBase,
    ChapterItem,
    ComicBookItem,
    Citem,
    SearchResultItem)
from ..exceptions import ChapterNotFound, ComicbookNotFound

logger = logging.getLogger(__name__)

class KuaiKanCrawler(CrawlerBase):

    SITE = "kuaikan"
    SOURCE_NAME = "快看漫画"
    DEFAULT_COMICID = 1338
    DEFAULT_COMIC_NAME = '海贼王'

    def __init__(self, comicid=None):
        try:
            execjs.get()
        except Exception:
            raise RuntimeError('请先安装nodejs。 https://nodejs.org/zh-cn/')
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return "https://www.kuaikanmanhua.com/web/topic/{}/".format(self.comicid)

    def parse_api_data_from_page(self, html):
        r = re.search('<script>window.__NUXT__=(.*?);</script>', html, re.S)
        if not r:
            return
        js_str = r.group(1)
        r = execjs.eval(js_str)
        return r['data'][0]

    def get_comicbook_item(self):
        html = self.get_html(self.source_url)
        data = self.parse_api_data_from_page(html)
        if not data:
            raise ComicbookNotFound.from_template(site=self.SITE,
                                                  comicid=self.comicid,
                                                  source_url=self.source_url)
        name = data['topicInfo']['title']
        author = data['topicInfo']['user']['nickname']
        desc = data['topicInfo']['description']
        tag = ",".join(data['topicInfo']['tags'])
        cover_image_url = data['topicInfo']['cover_image_url']
        citem_dict = {}
        comics = sorted(data['comics'], key=lambda x: x['id'])
        for idx, c in enumerate(comics, start=1):
            chapter_number = idx
            title = c['title']
            cid = c['id']
            citem_dict[chapter_number] = Citem(
                chapter_number=chapter_number,
                cid=cid,
                title=title)

        return ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             cover_image_url=cover_image_url,
                             author=author,
                             source_url=self.source_url,
                             source_name=self.SOURCE_NAME,
                             citem_dict=citem_dict)

    def get_chapter_soure_url(self, cid):
        return 'https://www.kuaikanmanhua.com/web/comic/{}/'.format(cid)

    def get_chapter_item(self, citem):
        url = self.get_chapter_soure_url(citem.cid)
        html = self.get_html(url)
        data = self.parse_api_data_from_page(html)
        if not data:
            raise ChapterNotFound.from_template(site=self.SITE,
                                                comicid=self.comicid,
                                                chapter_number=citem.chapter_number,
                                                source_url=self.source_url)
        image_urls = [i['url'] for i in data['comicInfo']['comicImages']]
        source_url = self.get_chapter_soure_url(cid=citem.cid)
        return ChapterItem(chapter_number=citem.chapter_number,
                           title=citem.title,
                           image_urls=image_urls,
                           source_url=source_url)

    def search(self, name):
        url = 'https://www.kuaikanmanhua.com/s/result/{}'.format(name)
        html = self.get_html(url)
        data = self.parse_api_data_from_page(html)
        rv = []
        for i in data['resultList']:
            comicid = i['url'].split('/')[-1]
            name = i['title']
            cover_image_url = i['image_url']
            source_url = 'https://www.kuaikanmanhua.com' + i['url']
            search_result_item = SearchResultItem(site=self.SITE,
                                                  comicid=comicid,
                                                  name=name,
                                                  cover_image_url=cover_image_url,
                                                  source_url=source_url)
            rv.append(search_result_item)
        return rv

    def login(self):
        login_url = "https://www.kuaikanmanhua.com/webs/loginh?redirect=https%3A%2F%2Fwww.kuaikanmanhua.com%2F"
        self.selenium_login(login_url=login_url,
                            check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("passToken", domain=".kuaikanmanhua.com"):
            return True
