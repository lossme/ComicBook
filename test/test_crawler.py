import os
import logging

from onepiece.comicbook import ComicBook
from onepiece.session import SessionMgr
logger = logging.getLogger()


def _test_crawl_comicbook(site, comicid=None,
                          chapter_number=1, test_search=True):
    comicbook = ComicBook(site=site, comicid=comicid)
    proxy = os.environ.get('ONEPIECE_PROXY_{}'.format(site.upper())) or os.environ.get('ONEPIECE_PROXY')
    if proxy:
        SessionMgr.set_proxy(site=site, proxy=proxy)
    comicbook.start_crawler()
    chapter = comicbook.Chapter(chapter_number=chapter_number)
    assert len(chapter.image_urls) > 0

    logger.info(chapter.to_dict())
    logger.info(comicbook.to_dict())
    if test_search:
        result = comicbook.search(name=comicbook.crawler.DEFAULT_SEARCH_NAME)
        assert len(result.to_dict()) > 0
    return comicbook, chapter


def test_qq():
    # 海贼王  URL: https://ac.qq.com/Comic/ComicInfo/id/505430
    _test_crawl_comicbook(site='qq')


def test_u17():
    # 雏蜂 URL: http://www.u17.com/comic/195.html
    _test_crawl_comicbook(site='u17')


def test_bilibili():
    # 航海王 URL: https://manga.bilibili.com/detail/mc24742
    _test_crawl_comicbook(site='bilibili')


def test_kuaikan():
    # 航海王 URL: https://www.kuaikanmanhua.com/web/topic/1338/
    _test_crawl_comicbook(site='kuaikan')


def test_manhuagui():
    # 鬼灭之刃 URL: https://www.manhuagui.com/comic/19430
    _test_crawl_comicbook(site='manhuagui')


def test_18comic():
    _test_crawl_comicbook(site='18comic')


def test_nhentai():
    _test_crawl_comicbook(site='nhentai')


def test_wnacg():
    _test_crawl_comicbook(site='wnacg')


def test_manhuatai():
    _test_crawl_comicbook(site='manhuatai', test_search=False)


def test_acg456():
    _test_crawl_comicbook(site='acg456', test_search=False)


def test_mh1234():
    _test_crawl_comicbook(site='mh1234')


def test_77mh():
    _test_crawl_comicbook(site='77mh')


def test_dmzj():
    _test_crawl_comicbook(site='dmzj')


def test_dm5():
    _test_crawl_comicbook(site='dm5')


def test_manhuadb():
    _test_crawl_comicbook(site='manhuadb')


def test_36mh():
    _test_crawl_comicbook(site='36mh', test_search=False)


def test_gufengmh8():
    _test_crawl_comicbook(site='gufengmh8', test_search=False)


def test_mh160():
    _test_crawl_comicbook(site='mh160')


def test_tuhao456():
    _test_crawl_comicbook(site='tuhao456')


def test_177pic():
    _test_crawl_comicbook(site='177pic')


def test_18h():
    _test_crawl_comicbook(site='18h')
