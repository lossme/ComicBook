import requests

from ..exceptions import ChapterSourceNotFound


class ComicBookCrawler():

    HEADERS = {
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/65.0.3325.146 Safari/537.36')
    }
    TIMEOUT = 30
    source_name = '鼠绘漫画'
    session = requests.session()

    def __init__(self, comicid):
        self.comicid = comicid
        self.api_data = None
        # {int_chapter_number: chapter_api_data}
        self.chapter_api_data_db = {}

    @classmethod
    def send_request(cls, url, **kwargs):
        kwargs.setdefault('headers', cls.HEADERS)
        kwargs.setdefault('timeout', cls.TIMEOUT)
        return cls.session.get(url, **kwargs)

    @classmethod
    def get_json(cls, url):
        response = cls.send_request(url)
        return response.json()

    @classmethod
    def get_html(cls, url):
        response = cls.send_request(url)
        return response.text

    def get_api_data(self):
        if self.api_data is not None:
            return self.api_data
        # https://prod-api.ishuhui.com/ver/8a175090/anime/detail?id=1&type=comics&.json
        url = "https://prod-api.ishuhui.com/ver/8a175090/anime/detail?id={}&type=comics&.json"
        url = url.format(self.comicid)
        data = self.get_json(url=url)
        self.api_data = data
        return self.api_data

    def get_chapter_api_data(self, chapter_number):
        if chapter_number in self.chapter_api_data_db:
            return self.chapter_api_data_db[chapter_number]

        str_chapter_number = str(chapter_number)
        api_data = self.get_api_data()
        for items in api_data['data']['comicsIndexes']['1']['nums'].values():
            if str_chapter_number in items:
                chapter_data_sources = items[str_chapter_number]
                for chapter_data in chapter_data_sources:
                    if chapter_data['sourceID'] == 1:
                        # https://prod-api.ishuhui.com/comics/detail?id=11196
                        url = "https://prod-api.ishuhui.com/comics/detail?id={}".format(chapter_data['id'])
                        chapter_api_data = self.get_json(url)
                        self.chapter_api_data_db[chapter_number] = chapter_api_data
                    if chapter_data['sourceID'] == 2:
                        # http://ac.qq.com/ComicView/index/id/505430/cid/1
                        # qq_source_url = chapter_data['url']
                        pass
        if chapter_number not in self.chapter_api_data_db:
            raise ChapterSourceNotFound("没找到资源 {} {}".format(self.get_comicbook_name(), chapter_number))
        return self.chapter_api_data_db[chapter_number]

    def get_comicbook_name(self):
        api_data = self.get_api_data()
        return api_data['data']['name']

    def get_comicbook_desc(self):
        api_data = self.get_api_data()
        return api_data['data']['desc']

    def get_comicbook_tag(self):
        api_data = self.get_api_data()
        return api_data['data']['tag']

    def get_max_chapter_number(self):
        api_data = self.get_api_data()
        return int(api_data['data']['comicsIndexes']['1']['maxNum'])

    def create_chapter(self, url):
        # https://prod-api.ishuhui.com/comics/detail?id=11196
        data = self.get_json(url)
        images = [ImageInfo(item['url']) for item in data['data']['contentImg']]
        return images

    def get_chapter_title(self, chapter_number):
        chapter_api_data = self.get_chapter_api_data(chapter_number)
        return chapter_api_data['data']['title']

    def get_chapter_image_urls(self, chapter_number):
        chapter_api_data = self.get_chapter_api_data(chapter_number)
        return [item['url'] for item in chapter_api_data['data']['contentImg']]
