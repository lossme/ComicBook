class ComicbookCrawlerException(Exception):
    pass


class NotFoundError(ComicbookCrawlerException):
    pass


class ComicbookNotFound(NotFoundError):
    pass


class ChapterSourceNotFound(NotFoundError):
    pass


class ImageDownloadError(ComicbookCrawlerException):
    pass


class URLException(ComicbookCrawlerException):
    pass
