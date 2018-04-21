from onepiece.site.qq import QQComicBook
from onepiece.site.ishuhui import IshuhuiComicBook


class ComicBook:
    def __new__(cls, args):
        if args.site == 'qq':
            return QQComicBook(args)
        elif args.site == 'ishuhui':
            return IshuhuiComicBook(args)
