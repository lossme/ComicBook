from . import ComicBookCrawlerBase, ChapterItem, ComicBookItem
from ..exceptions import ChapterSourceNotFound


class ComicBookCrawler(ComicBookCrawlerBase):
    source_name = '狱友提供'
    site = "yuyou"

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid

    def get_comicbook_item(self):
        return ComicBookItem(name="狱友提供", desc="", tag="", max_chapter_number=1914)

    def get_chapter_item(self, chapter_number):
        if 97 > chapter_number or chapter_number > 1914:
            raise ChapterSourceNotFound()
        url = "http://182.61.35.52:8087/laidianwebapp/selectDetailsPost?id={}".format(chapter_number)
        response = self.session.post(url=url)
        if response.status_code != 200:
            raise ChapterSourceNotFound("error url={} code={}".format(url, response.status_code))

        data = response.json()
        title = "{name}-{utelephone}-{title}"\
            .format(name=data["data"]["postName"],
                    utelephone=data["data"]["utelephone"],
                    title=data["data"]["postText"])
        image_urls = [data["data"]["image{}".format(i)].replace("vhttp", "http", 1) for i in range(1, 5)]
        image_urls = list(filter(lambda x: bool(x), image_urls))

        return ChapterItem(chapter_number=chapter_number, title=title, image_urls=image_urls)
