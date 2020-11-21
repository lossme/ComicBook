import re
import logging
from urllib.parse import urljoin

import execjs

from ..crawlerbase import CrawlerBase
from ..exceptions import ChapterNotFound, ComicbookNotFound

logger = logging.getLogger(__name__)


class KuaiKanCrawler(CrawlerBase):

    SITE = "kuaikan"
    SITE_INDEX = 'https://www.kuaikanmanhua.com/'
    SOURCE_NAME = "快看漫画"

    LOGIN_URL = urljoin(SITE_INDEX, "/webs/loginh?redirect={}".format(SITE_INDEX))
    DEFAULT_COMICID = 1338
    DEFAULT_SEARCH_NAME = '海贼王'
    DEFAULT_TAG = 'tag_0'

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/web/topic/{}/".format(comicid))

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
        cover_image_url = data['topicInfo']['cover_image_url']
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
        for idx, c in enumerate(reversed(data['comics']), start=1):
            chapter_number = idx
            title = c['title']
            cid = c['id']
            url = self.get_chapter_soure_url(cid)
            book.add_chapter(chapter_number=chapter_number, source_url=url, title=title)
        for tag_name in data['topicInfo']['tags']:
            tag_id = self.get_tag_id_by_name(tag_name)
            book.add_tag(name=tag_name, tag=tag_id)
        return book

    def get_chapter_soure_url(self, cid):
        return urljoin(self.SITE_INDEX, "/web/comic/{}/".format(cid))

    def get_chapter_item(self, citem):
        html = self.get_html(citem.source_url)
        data = self.parse_api_data_from_page(html)
        if not data:
            raise ChapterNotFound.from_template(site=self.SITE,
                                                comicid=self.comicid,
                                                chapter_number=citem.chapter_number,
                                                source_url=self.source_url)
        image_urls = [i['url'] for i in data['comicInfo']['comicImages']]
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def search(self, name, page=1, size=None):
        if page != 1:
            return []
        url = urljoin(self.SITE_INDEX, "/s/result/{}/".format(name))
        html = self.get_html(url)
        data = self.parse_api_data_from_page(html)
        result = self.new_search_result_item()
        for i in data['resultList']:
            comicid = i['url'].split('/')[-1]
            name = i['title']
            cover_image_url = i['image_url']
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def latest(self, page=1):
        pos = page - 1
        url = 'https://www.kuaikanmanhua.com/v2/pweb/daily/topics?pos=%s' % pos
        data = self.get_json(url)
        result = self.new_search_result_item()
        for i in data['data']['topics']:
            comicid = i['id']
            name = i['title']
            cover_image_url = i['cover_image_url']
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        url = "https://www.kuaikanmanhua.com/tag/0?state=1&sort=1&page=1"
        html = self.get_html(url)
        data = self.parse_api_data_from_page(html)
        tags = self.new_tags_item()
        for i in data['res']['data']['tags']:
            category = '题材'
            name = i['title']
            tag_id = i['tag_id']
            tag = 'tag_id_%s' % tag_id
            tags.add_tag(category=category, name=name, tag=tag)
        for i in data['res']['data']['update_status']:
            category = '进度'
            name = i['description']
            code = i['code']
            tag = 'state_%s' % code
            tags.add_tag(category=category, name=name, tag=tag)
        return tags

    def get_tag_result(self, tag, page=1):
        params = {'page': page}
        if tag:
            for i in tag.split(','):
                key, value = i.rsplit('_', 1)
                params[key] = value
        tag_id = params.pop('tag_id', 0)
        url = 'https://www.kuaikanmanhua.com/tag/%s' % tag_id
        html = self.get_html(url, params=params)
        data = self.parse_api_data_from_page(html)
        result = self.new_search_result_item()
        for i in data['res']['data']['topics']:
            comicid = i['id']
            name = i['title']
            cover_image_url = i['cover_image_url']
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def login(self):
        self.selenium_login(login_url=self.LOGIN_URL,
                            check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("passToken", domain=".kuaikanmanhua.com"):
            return True
