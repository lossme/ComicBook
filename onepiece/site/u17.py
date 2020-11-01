import urllib.parse
import logging

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class U17Crawler(CrawlerBase):

    SOURCE_NAME = "有妖气"
    SITE = "u17"
    SITE_INDEX = 'https://www.u17.com/'

    COMIC_BOOK_API = "https://www.u17.com/comic/ajax.php?mod=chapter&act=get_chapter_list&comic_id={comicid}"
    CHAPTER_API = "https://www.u17.com/comic/ajax.php?mod=chapter&act=get_chapter_v5&chapter_id={chapter_id}"
    CHAPTER_URL = "https://www.u17.com/chapter/{chapter_id}.html"
    LOGIN_URL = "https://passport.u17.com/member_v2/login.php?url=https://www.u17.com/"

    DEFAULT_COMICID = 195
    DEFAULT_SEARCH_NAME = '雏蜂'
    DEFAULT_TAG = 'th_104'

    STATUS_MAP = {
        "0": '连载中',
        "1": '完结',
        "2": '新作',
    }

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return "https://www.u17.com/comic/{}.html".format(comicid)

    def get_comicbook_item(self):
        url = self.COMIC_BOOK_API.format(comicid=self.comicid)
        soup = self.get_soup(self.source_url)
        api_data = self.get_json(url)
        name = api_data['comic_info']['name']
        desc = api_data['comic_info']['description']
        cover_image_url = api_data['comic_info']['cover']
        author = api_data['comic_info']['author_name']
        author = api_data['comic_info']['author_name']
        status = self.STATUS_MAP.get(api_data['comic_info']['series_status'], "")
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url,
                                       status=status)
        for a in soup.find('div', {'class': 'line1'}).find_all('a'):
            tag_name = a.text.strip()
            tag_id = self.get_tag_id_by_name(tag_name)
            book.add_tag(name=tag_name, tag=tag_id)

        for idx, item in enumerate(api_data['chapter_list'], start=1):
            chapter_number = idx
            chapter_id = item['chapter_id']
            title = item['name']
            chapter_url = self.CHAPTER_URL.format(chapter_id=chapter_id)
            book.add_chapter(chapter_number=chapter_number, title=title,
                             source_url=chapter_url, chapter_id=chapter_id)
        return book

    def get_chapter_item(self, citem):
        chapter_id = citem.chapter_id
        chapter_api_url = self.CHAPTER_API.format(chapter_id=chapter_id)
        data = self.get_json(chapter_api_url)
        title = data["chapter"]["name"]
        image_urls = []
        for item in data["image_list"]:
            image_urls.append(item['src'])
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def search(self, name, page=1, size=None):
        url = "http://so.u17.com/all/{}/m0_p{}.html".format(urllib.parse.quote(name), page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('div', {'class': 'comiclist'}).find_all('li'):
            cover_image_url = li.find('div', {'class': 'cover'}).img.get('src')
            name = li.find('div', {'class': 'info'}).h3.strong.a.text.strip()
            href = li.find('div', {'class': 'cover'}).a.get('href')
            comicid = href.rsplit('/', 1)[-1].split('.')[0]
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def latest(self, page=1):
        url = 'https://www.u17.com/comic/ajax.php?mod=comic_list&act=comic_list_new_fun&a=get_comic_list'
        params = {
            'data[order]': 1,
            'data[page_num]': page,
            'data[group_id]': 'no',
            'data[theme_id]': 'no',
            'data[is_vip]': 'no',
            'data[accredit]': 'no',
            'data[color]': 'no',
            'data[comic_type]': 'no',
            'data[series_status]': 'no',
            'data[read_mode]': 'no'
        }
        response = self.send_request('POST', url, data=params)
        data = response.json()
        result = self.new_search_result_item()
        for i in data['comic_list']:
            cover_image_url = i['cover']
            comicid = i['comic_id']
            name = i['name']
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        url = "https://www.u17.com/comic_list/th99_gr99_ca99_ss99_ob0_ac0_as0_wm0_co99_ct99_p1.html?order=2"
        soup = self.get_soup(url)
        tags = self.new_tags_item()
        for div in soup.find_all('div', {'class': 'categray_box'}):
            category = div.h2.text
            for li in div.find_all('li'):
                name = li.text
                tag = li.get('id')
                tags.add_tag(category=category, name=name, tag=tag)
        return tags

    def get_tag_result(self, tag, page):
        url = 'https://www.u17.com/comic/ajax.php?mod=comic_list&act=comic_list_new_fun&a=get_comic_list'
        params = {
            'data[order]': 1,
            'data[page_num]': page,
            'data[group_id]': 'no',
            'data[theme_id]': 'no',
            'data[is_vip]': 'no',
            'data[accredit]': 'no',
            'data[color]': 'no',
            'data[comic_type]': 'no',
            'data[series_status]': 'no',
            'data[read_mode]': 'no'
        }
        if tag:
            for i in tag.split(','):
                key, value = i.rsplit('_', 1)
                if value == 'all':
                    continue
                if key == 'th':
                    params['data[theme_id]'] = value
                elif key == 'iv':
                    params['data[is_vip]'] = value
                elif key == 'ac':
                    params['data[accredit]'] = value
                elif key == 'ct':
                    params['data[comic_type]'] = value
                elif key == 'ss':
                    params['data[series_status]'] = value
                elif key == 'rm':
                    params['data[read_mode]'] = value
        response = self.send_request('POST', url, data=params)
        data = response.json()
        result = self.new_search_result_item()
        for i in data['comic_list']:
            cover_image_url = i['cover']
            comicid = i['comic_id']
            name = i['name']
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def login(self):
        self.selenium_login(
            login_url=self.LOGIN_URL, check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("xxauthkey", domain=".u17.com"):
            return True
