import re
import logging
from urllib.parse import urljoin

from PIL import Image
from bs4 import BeautifulSoup

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class C18comicCrawler(CrawlerBase):

    SITE = "18comic"
    SITE_INDEX = 'https://18comic.org/'
    SOURCE_NAME = "禁漫天堂"
    LOGIN_URL = SITE_INDEX
    R18 = True

    DEFAULT_COMICID = 201118
    DEFAULT_SEARCH_NAME = '騎馬的女孩好想被她騎'
    DEFAULT_TAG = 'CG集'

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/album/{}/".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.find('div', {'itemprop': 'name'}).text.strip()
        author = ''
        desc = ''
        for i in soup.find_all('div', {'class': 'p-t-5 p-b-5'}):
            if '敘述：' in i.text:
                desc = i.text.strip().replace('\n', '').replace('敘述：', '', 1)
        for i in soup.find_all('div', {'class': 'tag-block'}):
            if '作者：' in i.text:
                author = i.text.strip().replace('\n', '').replace('作者：', '', 1)
        cover_image_url = soup.find('img', {'itemprop': 'image'}).get('src')
        res = soup.find('div', {'class': 'episode'})
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
        for a in soup.find('span', {'itemprop': 'genre'}).find_all('a'):
            tag_name = a.text.strip()
            book.add_tag(name=tag_name, tag=tag_name)
        if not res:
            chapter_number = 1
            url = urljoin(self.SITE_INDEX, '/photo/{}/'.format(self.comicid))
            book.add_chapter(chapter_number=chapter_number, source_url=url, title=str(chapter_number))
        else:
            a_list = res.find_all('a')
            for idx, a_soup in enumerate(a_list, start=1):
                chapter_number = idx
                for i in a_soup.find_all('span'):
                    i.decompose()
                title = a_soup.text.strip().replace('\n', ' ')
                url = a_soup.get('href')
                full_url = urljoin(self.SITE_INDEX, url)
                book.add_chapter(chapter_number=chapter_number, source_url=full_url, title=title)
        return book

    def get_chapter_item(self, citem):
        html = self.get_html(citem.source_url)
        soup = BeautifulSoup(html, 'html.parser')
        scramble_id = re.search(r'var scramble_id = (\d+);', html).group(1)
        aid = re.search(r'var aid = (\d+);', html).group(1)
        img_list = soup.find('div', 'row thumb-overlay-albums')\
            .find_all('img', {'id': re.compile(r'album_photo_\d+')})
        image_urls = []
        image_pipelines = []
        for img_soup in img_list:
            url = img_soup.get('data-original')
            if not url:
                url = img_soup.get('src')

            if url.index('.jpg') < 0 or int(aid) < int(scramble_id):
                image_pipelines.append(None)
            else:
                image_pipelines.append(self.image_pipeline)

            image_urls.append(url)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     image_pipelines=image_pipelines,
                                     source_url=citem.source_url)

    def image_pipeline(self, image_path):
        img = Image.open(image_path)
        width, height = img.size
        num = 10
        one_piece = int(height / num)
        regions = []
        for i in range(num):
            h_start = (one_piece * i)
            h_end = (one_piece * (i + 1))
            box = (0, h_start, width, h_end)
            region = img.crop(box)
            regions.append(region)
        new_img = Image.new(img.mode, img.size)
        for i, region in enumerate(reversed(regions)):
            h_start = (one_piece * i)
            h_end = (one_piece * (i + 1))
            box = (0, h_start, width, h_end)
            new_img.paste(region, box=box)
        img.close()
        new_img.save(image_path, quality=95)

    def search(self, name, page=1, size=None):
        url = urljoin(
            self.SITE_INDEX,
            '/search/photos?search_query={}&page={}'.format(name, page)
        )
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for div in soup.find_all('div', {'class': 'thumb-overlay'}):
            comicid = div.a.get('id').split('_')[-1]
            name = div.img.get('alt')
            cover_image_url = div.img.get('data-original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def latest(self, page=1):
        url = 'https://18comic.org/albums?o=mr&page=%s' % page
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for div in soup.find_all('div', {'class': 'thumb-overlay-albums'}):
            comicid = div.a.get('id').split('_')[-1]
            name = div.img.get('alt')
            cover_image_url = div.img.get('data-original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        url = "https://18comic.org/theme/"
        soup = self.get_soup(url)

        div_list = soup.find('div', {'id': 'wrapper'}).find('div', {'class': 'container'})\
            .find_all('div', {'class': 'row'})
        tags = self.new_tags_item()
        for div in div_list:
            h4 = div.h4
            if not h4:
                continue
            category = h4.text
            for li in div.find_all('li'):
                name = li.a.text
                tags.add_tag(category=category, name=name, tag=name)
        return tags

    def get_tag_result(self, tag, page=1):
        return self.search(name=tag, page=page)

    def login(self):
        self.selenium_login(login_url=self.LOGIN_URL,
                            check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("remember", domain=".18comic.org"):
            return True
