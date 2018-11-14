import requests
import functools
import warnings

from ..comicbook import ComicBook, Chapter, ImageInfo


class ComicBookCrawler():

    HEADERS = {
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/65.0.3325.146 Safari/537.36')
    }
    TIMEOUT = 30
    source_name = '鼠绘漫画'
    session = requests.session()

    def __init__(self, comicid):
        pass

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

    @classmethod
    def create_comicbook(cls, comicid):
        # https://prod-api.ishuhui.com/ver/8a175090/anime/detail?id=1&type=comics&.json
        url = "https://prod-api.ishuhui.com/ver/8a175090/anime/detail?id={}&type=comics&.json".format(comicid)
        data = cls.get_json(url)
        name = data['data']['name']
        desc = data['data']['desc']
        tag = data['data']['tag']

        max_chapter_number = data['data']['comicsIndexes']['1']['maxNum']
        comicbook = ComicBook(name=name, desc=desc, tag=tag, source_name=cls.source_name)
        comicbook._data = data

        comicbook.get_max_chapter_number = lambda: max_chapter_number
        comicbook.get_chapter = functools.partial(cls.get_chapter, comicbook=comicbook)
        comicbook.get_all_chapter = functools.partial(cls.get_all_chapter, comicbook=comicbook)
        return comicbook

    @classmethod
    def get_all_chapter(cls, comicbook):
        for chapter_number in range(1, comicbook.max_chapter_number + 1):
            try:
                yield cls.get_chapter(chapter_number=chapter_number, comicbook=comicbook)
            except Exception as e:
                warnings.warn(str(e))

    @classmethod
    def get_chapter(cls, chapter_number, comicbook):
        max_chapter_number = int(comicbook.get_max_chapter_number())
        if int(chapter_number) < 0:
            chapter_number = max_chapter_number + chapter_number + 1

        chapter_number = str(chapter_number)
        for items in comicbook._data['data']['comicsIndexes']['1']['nums'].values():
            if chapter_number in items:
                chapter_data_sources = items[chapter_number]
                for chapter_data in chapter_data_sources:
                    if chapter_data['sourceID'] == 1:
                        title = chapter_data['title']
                        url = "https://prod-api.ishuhui.com/comics/detail?id={}".format(chapter_data['id'])
                        chapter = Chapter(title=title, chapter_number=chapter_number)
                        chapter.get_chapter_images = functools.partial(cls.get_chapter_images,
                                                                       url=url,
                                                                       comicbook=comicbook)
                        return chapter
                    if chapter_data['sourceID'] == 2:
                        # http://ac.qq.com/ComicView/index/id/505430/cid/1
                        # qq_source_url = chapter_data['url']
                        pass

        raise Exception("没找到资源 {} {}".format(comicbook.name, chapter_number))

    @classmethod
    def get_chapter_images(cls, url, comicbook):
        # https://prod-api.ishuhui.com/comics/detail?id=11196
        data = cls.get_json(url)
        images = [ImageInfo(item['url']) for item in data['data']['contentImg']]
        return images
