class ComicbookException(Exception):
    pass


class NotFoundError(ComicbookException):
    pass


class ComicbookNotFound(NotFoundError):
    TEMPLATE = ("资源未找到！ site={site} comicid={comicid} "
                "source_url={source_url}")


class ChapterNotFound(NotFoundError):
    TEMPLATE = ("资源未找到！ site={site} comicid={comicid} "
                "chapter_number={chapter_number} source_url={source_url}")


class URLException(ComicbookException):
    pass


class SiteNotSupport(ComicbookException):
    pass


class ImageDownloadError(ComicbookException):
    pass
