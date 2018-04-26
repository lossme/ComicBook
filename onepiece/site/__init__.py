from .qq import QQComicBook
from .ishuhui import IshuhuiComicBook


class ComicBook:

    @staticmethod
    def create(site):
        if site == 'qq':
            return QQComicBook()
        elif site == 'ishuhui':
            return IshuhuiComicBook()
