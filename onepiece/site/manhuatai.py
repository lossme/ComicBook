import re
import logging
from urllib.parse import urljoin

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class ManhuataiCrawler(CrawlerBase):

    SITE = "manhuatai"
    SITE_INDEX = 'https://www.manhuatai.com/'
    SOURCE_NAME = "漫画台"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = "doupocangqiong"
    DEFAULT_SEARCH_NAME = '斗破苍穹'
    DEFAULT_TAG = ""

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, str(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.find('h1', {'id': 'detail-title'}).text.strip()
        comic_id = soup.find('h1', {'id': 'detail-title'}).get('data-comic-id')
        author = ''
        desc = soup.find('p', {'class': 'desc-content'}).text
        last_update_time_text = soup.find('span', {'class': 'update'}).text
        last_update_time = re.search(r'(\d{4}-\d{2}-\d{2})', last_update_time_text).group(1)

        cover_image_url = "https:" + soup.find('div', {'class': 'detail-cover'}).img.get('data-src')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url,
                                       last_update_time=last_update_time)
        for a in soup.find('ul', {'class': 'tags'}).find_all('a'):
            tag_name = a.text.strip()
            book.add_tag(name=tag_name, tag='')

        li_list = soup.find('ol', {'id': 'j_chapter_list'}).find_all('li')
        for idx, li in enumerate(li_list, start=1):
            chapter_number = idx
            title = li.a.get('title')
            href = li.a.get('href')
            url = urljoin(self.SITE_INDEX, href)
            cid = li.get('data-chapter')
            chapter_newid = href.rsplit('/', 1)[-1].rsplit('.', 1)[0]
            title = li.a.get('title')
            book.add_chapter(
                chapter_number=chapter_number,
                source_url=url,
                title=title,
                comic_id=comic_id,
                cid=cid,
                chapter_newid=chapter_newid,
            )
        return book

    def get_chapter_item(self, citem):
        params = {
            'product_id': 2,
            'productname': 'mht',
            'platformname': 'pc',
            'comic_id': citem.comic_id,
            'chapter_newid': citem.chapter_newid,
        }
        url = "https://www.manhuatai.com/api/getchapterinfo"
        data = self.get_json(url, params=params)
        image_urls = []
        prefix = "https://mhpic.jumanhua.com"
        rule = data['data']['current_chapter']['rule']
        total = data['data']['current_chapter']['end_num']
        for i in range(1, total + 1):
            url = prefix + rule.replace('$$', str(i)) + '-mht.middle.webp'
            image_urls.append(url)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        result = self.new_search_result_item()

        url = "https://www.manhuatai.com/gengxin/"
        soup = self.get_soup(url)
        div_list = soup.find_all('div', {'class': 'J_weekDataList'})
        for div in div_list:
            for li in div.ul.find_all('li'):
                href = li.a.get('href')
                name = li.a.get('title')
                comicid = href.strip('/')
                cover_image_url = 'http:' + li.img.get('data-src')
                source_url = self.get_source_url(comicid)
                result.add_result(comicid=comicid,
                                  name=name,
                                  cover_image_url=cover_image_url,
                                  source_url=source_url)
        return result
