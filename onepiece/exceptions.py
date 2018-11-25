class ComicbookCrawlerException(Exception):
    pass


class ComicbookNotFound(Exception):
    pass


class ChapterSourceNotFound(ComicbookCrawlerException):
    pass


class ImageDownloadError(ComicbookCrawlerException):
    pass
