import re
from . import ComicBookCrawlerBase, Chapter, ComicBook
from ..exceptions import ChapterSourceNotFound


class ComicBookCrawler(ComicBookCrawlerBase):

    source_name = '鼠绘漫画'
    CHAPTER_INTERVAL_PATTERN = re.compile(r"^(?P<start_chapter_number>\d+)\-(?P<end_chapter_number>\d+)")

    def __init__(self, comicid):
        super().__init__()
        self.comicid = comicid
        self.api_data = None
        self._comics_ver = None

    @property
    def comics_ver(self):
        if self._comics_ver is None:
            url = "https://prod-u.ishuhui.com/ver"
            data = self.get_json(url)
            self._comics_ver = data["data"]["comics"]
        self._comics_ver

    def get_api_data(self):
        if self.api_data:
            return self.api_data
        # https://prod-api.ishuhui.com/ver/8a175090/anime/detail?id=1&type=comics&.json
        url = "https://prod-api.ishuhui.com/ver/{ver}/anime/detail?id={comicid}&type=comics&.json"
        url = url.format(ver=self.comics_ver, comicid=self.comicid)
        self.api_data = self.get_json(url=url)
        return self.api_data

    def get_comicbook(self):
        api_data = self.get_api_data()
        comicbook = self.parser_api_data(api_data)
        return comicbook

    def get_chapter(self, chapter_number):
        api_data = self.get_api_data()
        for interval, items in api_data['data']['comicsIndexes']['1']['nums'].items():
            for str_chapter_number, chapter_data_sources in items.items():
                # str_chapter_number = "1-8"
                # str_chapter_number = "9-17"
                r = self.CHAPTER_INTERVAL_PATTERN.search(str_chapter_number)
                if r:
                    _chapter_number = int(r.group("start_chapter_number"))
                else:
                    _chapter_number = int(str_chapter_number)
                if chapter_number != _chapter_number:
                    continue

                for chapter_data in chapter_data_sources:
                    source_id = chapter_data['sourceID']
                    if source_id in [1, 7]:
                        # https://prod-api.ishuhui.com/comics/detail?id=11196
                        url = "https://prod-api.ishuhui.com/comics/detail?id={}".format(chapter_data['id'])
                        chapter_api_data = self.get_json(url)
                        chapter = self.parser_ishuihui_source(chapter_api_data)
                        return chapter
                    elif chapter_data['sourceID'] == 2:
                        # http://ac.qq.com/ComicView/index/id/505430/cid/1
                        qq_source_url = chapter_data['url']
                        html = self.get_html(qq_source_url)
                        chapter = self.parser_qq_source(html)
                        return chapter
                    if chapter_data['sourceID'] == 6:
                        # 百度网盘
                        pass
        raise ChapterSourceNotFound()

    @classmethod
    def parser_api_data(cls, api_data):
        name = api_data['data']['name']
        desc = api_data['data']['desc']
        tag = api_data['data']['tag']
        max_chapter_number = int(api_data['data']['comicsIndexes']['1']['maxNum'])
        return ComicBook(name=name, desc=desc, tag=tag, max_chapter_number=max_chapter_number)

    @classmethod
    def parser_ishuihui_source(cls, chapter_api_data):
        # https://prod-api.ishuhui.com/comics/detail?id=11196
        image_urls = [item['url'] for item in chapter_api_data['data']['contentImg']]
        chapter_title = chapter_api_data['data']['title']
        return Chapter(title=chapter_title, image_urls=image_urls)

    @classmethod
    def parser_qq_source(self, chapter_page_html):
        # http://ac.qq.com/ComicView/index/id/505430/cid/1
        from .qq import ComicBookCrawler as QQComicBookCrawler
        return QQComicBookCrawler.parser_chapter_page(chapter_page_html)
