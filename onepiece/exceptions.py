class ComicbookException(Exception):
    pass


class NotFoundError(ComicbookException):
    pass


class ComicbookNotFound(NotFoundError):
    pass


class ChapterNotFound(NotFoundError):
    pass


class URLException(ComicbookException):
    pass


class SiteNotSupport(ComicbookException):
    pass


class ImageDownloadError(ComicbookException):
    pass
