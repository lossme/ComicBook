from . import ComicBookCrawlerBase
from ..exceptions import ChapterSourceNotFound


class ComicBookCrawler(ComicBookCrawlerBase):

    source_name = '鼠绘漫画'

    def __init__(self, comicid):
        super().__init__()
        self.comicid = comicid
        self.api_data = None

    def get_api_data(self):
        if self.api_data:
            return self.api_data
        # https://prod-api.ishuhui.com/ver/8a175090/anime/detail?id=1&type=comics&.json
        url = "https://prod-api.ishuhui.com/ver/8a175090/anime/detail?id={}&type=comics&.json"
        url = url.format(self.comicid)
        self.api_data = self.get_json(url=url)
        return self.api_data

    def get_comicbook(self):
        api_data = self.get_api_data()
        comicbook = self.parser_api_data(api_data)
        return comicbook

    def get_chapter(self, chapter_number):
        str_chapter_number = str(chapter_number)
        api_data = self.get_api_data()
        for items in api_data['data']['comicsIndexes']['1']['nums'].values():
            if str_chapter_number in items:
                chapter_data_sources = items[str_chapter_number]
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
        raise ChapterSourceNotFound("没找到资源 {} {}".format(self.get_comicbook_name(), chapter_number))

    @classmethod
    def parser_api_data(cls, api_data):
        name = api_data['data']['name']
        desc = api_data['data']['desc']
        tag = api_data['data']['tag']
        max_chapter_number = int(api_data['data']['comicsIndexes']['1']['maxNum'])
        return cls.ComicBook(name=name, desc=desc, tag=tag, max_chapter_number=max_chapter_number)

    @classmethod
    def parser_ishuihui_source(cls, chapter_api_data):
        # https://prod-api.ishuhui.com/comics/detail?id=11196
        image_urls = [item['url'] for item in chapter_api_data['data']['contentImg']]
        chapter_title = chapter_api_data['data']['title']
        return cls.Chapter(chapter_title=chapter_title, image_urls=image_urls)

    @classmethod
    def parser_qq_source(self, chapter_page_html):
        # http://ac.qq.com/ComicView/index/id/505430/cid/1
        from .qq import ComicBookCrawler as QQComicBookCrawler
        return QQComicBookCrawler.parser_chapter_page(chapter_page_html)
