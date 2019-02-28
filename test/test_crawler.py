from onepiece.comicbook import ComicBook


def crawl_comicbook(site, comicid, chapter_number):
    comicbook = ComicBook.create_comicbook(site=site, comicid=comicid)
    chapter = comicbook.Chapter(chapter_number=chapter_number)
    assert len(chapter.image_urls) > 0

    print(chapter.to_dict())
    print(comicbook.to_dict())
    return comicbook, chapter


def test_qq():
    # 海贼王  URL: https://ac.qq.com/Comic/ComicInfo/id/505430
    site = "qq"
    comicid = "505430"
    name = "海贼王"
    chapter_number = -1
    crawl_comicbook(site=site, comicid=comicid, chapter_number=chapter_number)

    result = ComicBook.search(site=site, name=name)
    assert len(result) > 0


def test_ishuhui():
    # 海贼王 URL: https://www.ishuhui.com/comics/anime/1
    site = "ishuhui"
    comicid = "1"
    name = "海贼王"
    chapter_number = -1
    crawl_comicbook(site=site, comicid=comicid, chapter_number=chapter_number)

    result = ComicBook.search(site=site, name=name)
    assert len(result) > 0


def test_wangyi():
    # 海贼王 URL: https://manhua.163.com/source/5015165829890111936
    site = "wangyi"
    comicid = "5015165829890111936"
    name = "海贼王"

    chapter_number = -1
    crawl_comicbook(site=site, comicid=comicid, chapter_number=chapter_number)

    result = ComicBook.search(site=site, name=name)
    assert len(result) > 0


def test_u17():
    # 雏蜂 URL: http://www.u17.com/comic/195.html
    site = "u17"
    comicid = "195"
    name = "雏蜂"
    chapter_number = -1
    crawl_comicbook(site=site, comicid=comicid, chapter_number=chapter_number)

    result = ComicBook.search(site=site, name=name)
    assert len(result) > 0
