from onepiece.site.qq import QQComicBook
from onepiece.site.ishuhui import IshuhuiComicBook


class ComicBook:

    @staticmethod
    def create(site):
        if site == 'qq':
            return QQComicBook()
        elif site == 'ishuhui':
            return IshuhuiComicBook()
