class ComicbookCrawlerException(Exception):
    pass


class ComicbookNotFound(ComicbookCrawlerException):
    pass


class ChapterSourceNotFound(ComicbookCrawlerException):
    pass


class ImageDownloadError(ComicbookCrawlerException):
    pass


class URLException(ComicbookCrawlerException):
    pass
