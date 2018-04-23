from onepiece.site.qq import QQComicBook
from onepiece.site.ishuhui import IshuhuiComicBook


class ComicBook:

    @classmethod
    def create(cls, site):
        if site == 'qq':
            return QQComicBook()
        elif site == 'ishuhui':
            return IshuhuiComicBook()
