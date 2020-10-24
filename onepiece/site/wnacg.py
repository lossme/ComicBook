import re
import logging
from urllib.parse import urljoin

import execjs

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class WnacgCrawler(CrawlerBase):

    SITE = "wnacg"
    SITE_INDEX = 'http://www.wnacg.org/'
    SOURCE_NAME = "绅士漫画"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = 106789
    DEFAULT_SEARCH_NAME = '过期米线线喵'
    DEFAULT_TAG = "3"
    REQUIRE_JAVASCRIPT = True
    R18 = True

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/photos-index-aid-{}".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.h2.text.strip()
        author = ''
        desc = soup.find('div', {'class': 'asTBcell uwconn'}).p.text
        tag = ''.join([i.text for i in
                       soup.find('div', {'class': 'addtags'}).find_all('a', {'class': 'tagshow'})])
        cover_image_url = "https:" + soup.find('div', {'class': 'asTBcell uwthumb'}).img.get('data-original')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       tag=tag,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
        chapter_number = 1
        url = urljoin(self.SITE_INDEX, '/photos-slide-aid-{}.html'.format(self.comicid))
        book.add_chapter(chapter_number=chapter_number, cid=self.comicid, source_url=url, title=str(chapter_number))
        return book

    def get_chapter_item(self, citem):
        api_url = urljoin(self.SITE_INDEX, "/photos-gallery-aid-{}.html".format(citem.cid))
        html = self.get_html(api_url)
        js = re.search(r'var (imglist.*?)\;\"\);\r', html).group(1)
        js_str = "fast_img_host=''," + js.replace('\\"', '"')
        img_list = execjs.eval(js_str)

        image_urls = []
        for i in img_list:
            url = i['url']
            if url.startswith('//'):
                image_urls.append('http:' + url)
            elif url.startswith('/'):
                image_urls.append(self.SITE_INDEX + url)
            else:
                image_urls.append(url)

        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def search(self, name, page=1, size=None):
        url = urljoin(
            self.SITE_INDEX,
            '/search/index.php?q={}&m=&f=_all&s=create_time_DESC&p={}'.format(name, page)
        )
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'class': 'cc'}).find_all('li'):
            href = li.a.get('href')
            name = li.a.get('title')
            name = re.sub(r'<[^>]+>', '', name, re.S)
            comicid = href.rsplit('.', 1)[0].split('-')[-1]
            cover_image_url = 'http:' + li.img.get('data-original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def latest(self, page=1):
        url = 'http://www.wnacg.org/albums-index-page-%s.html' % page
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'class': 'cc'}).find_all('li'):
            href = li.a.get('href')
            name = li.a.get('title')
            name = re.sub(r'<[^>]+>', '', name, re.S)
            comicid = href.rsplit('.', 1)[0].split('-')[-1]
            cover_image_url = 'http:' + li.img.get('data-original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    TAGS = [
        dict(name='同人志-全部', tag_id='5'),
        dict(name='同人志-汉化', tag_id='1'),
        dict(name='同人志-日语', tag_id='12'),
        dict(name='同人志-CG畫集', tag_id='2'),
        dict(name='同人志-Cosplay', tag_id='3'),
        dict(name='单行本-全部', tag_id='6'),
        dict(name='单行本-汉化', tag_id='9'),
        dict(name='单行本-日語', tag_id='13'),
    ]

    def get_tags(self):
        tags = self.new_tags_item()
        for i in self.TAGS:
            category, name = i['name'].split('-', 1)
            tag_id = i['tag_id']
            tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        if tag:
            url = 'http://www.wnacg.org/albums-index-page-%s-cate-%s.html' % (page, tag)
        else:
            url = "http://www.wnacg.org/albums.html"
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'class': 'cc'}).find_all('li'):
            href = li.a.get('href')
            name = li.a.get('title')
            name = re.sub(r'<[^>]+>', '', name, re.S)
            comicid = href.rsplit('.', 1)[0].split('-')[-1]
            cover_image_url = 'http:' + li.img.get('data-original')
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
        if session.cookies.get("remember", domain=".18comic.org"):
            return True
