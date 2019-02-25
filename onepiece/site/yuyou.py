from . import ComicBookCrawlerBase, ChapterItem, ComicBookItem
from ..exceptions import ChapterSourceNotFound


class ComicBookCrawler(ComicBookCrawlerBase):
    SOURCE_NAME = '狱友提供'
    SITE = "yuyou"

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid
        self.last_chapter_number = 1914
        self.min_chapter_number = 97

    def get_comicbook_item(self):
        return ComicBookItem(name="狱友提供", desc="", tag="", last_chapter_number=self.last_chapter_number)

    def get_chapter_item(self, chapter_number):
        if self.min_chapter_number > chapter_number or chapter_number > self.last_chapter_number:
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
        image_urls = []
        for i in range(1, 5):
            image_url = data["data"].get("image{}".format(i))
            if image_url:
                image_url = image_url.replace("vhttp", "http", 1)
                image_urls.append(image_url)
        return ChapterItem(chapter_number=chapter_number, title=title, image_urls=image_urls)
