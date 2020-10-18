class ComicbookException(Exception):
    pass


class NotFoundError(ComicbookException):
    pass


class ComicbookNotFound(NotFoundError):
    TEMPLATE = ("source not dound. site={site} comicid={comicid} "
                "source_url={source_url}")

    @classmethod
    def from_template(cls, **kwargs):
        msg = cls.TEMPLATE.format(**kwargs)
        return cls(msg)


class ChapterNotFound(NotFoundError):
    TEMPLATE = ("source not dound. site={site} comicid={comicid} "
                "chapter_number={chapter_number} source_url={source_url}")

    @classmethod
    def from_template(cls, **kwargs):
        msg = cls.TEMPLATE.format(**kwargs)
        return cls(msg)


class URLException(ComicbookException):
    pass


class SiteNotSupport(ComicbookException):
    pass


class ImageDownloadError(ComicbookException):
    pass
