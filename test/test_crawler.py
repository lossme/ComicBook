from onepiece.site.qq import ComicBookCrawler as QQComicBookCrawler
from onepiece.site.ishuhui import ComicBookCrawler as IshuhuiComicBookCrawler
from onepiece.site.wangyi import ComicBookCrawler as WangyiComicBookCrawler


def test_qq_crawler():
    """
    comicid="505430" # 海贼王
    URL: https://ac.qq.com/Comic/ComicInfo/id/505430
    """
    comicid = "505430"
    crawler = QQComicBookCrawler(comicid=comicid)

    comicbook_item = crawler.comicbook_item
    assert comicbook_item.name
    assert comicbook_item.max_chapter_number >= 933
    assert comicbook_item.author

    chapter_item = crawler.ChapterItem(chapter_number=933)
    assert chapter_item.title
    assert len(chapter_item.image_urls) > 0


def test_ishuhui_crawler():
    """
    comicid = "1" # 海贼王
    URL: https://prod-api.ishuhui.com/ver/fe058362/anime/detail?id=1&type=comics&.json"
    """
    comicid = "1"
    crawler = IshuhuiComicBookCrawler(comicid=comicid)

    comicbook_item = crawler.comicbook_item
    assert comicbook_item.name
    assert comicbook_item.max_chapter_number >= 933
    assert comicbook_item.author

    chapter_item = crawler.ChapterItem(chapter_number=933)
    assert chapter_item.title
    assert len(chapter_item.image_urls) > 0


def test_wangyi_crwaler():
    """
    comicid = "5015165829890111936" # 海贼王
    URL: https://manhua.163.com/source/5015165829890111936
    """
    comicid = "5015165829890111936"
    crawler = WangyiComicBookCrawler(comicid=comicid)

    comicbook_item = crawler.comicbook_item
    assert comicbook_item.name
    assert comicbook_item.max_chapter_number >= 933
    assert comicbook_item.author

    chapter_item = crawler.ChapterItem(chapter_number=934)
    assert chapter_item.title
    assert len(chapter_item.image_urls) > 0
