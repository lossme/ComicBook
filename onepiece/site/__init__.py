import importlib
import os
import re


HERE = os.path.abspath(os.path.dirname(__file__))


class ComicBook:
    ALL_SITE = list(
        map(
            lambda x: x.split(".py")[0],
            filter(
                lambda x: re.match(r"^[a-zA-Z].*?\.py$", x),
                os.listdir(HERE)
            )
        )
    )

    @staticmethod
    def create(site):
        if site not in ComicBook.ALL_SITE:
            raise Exception("site={} 暂不支持")

        module = importlib.import_module(".{}".format(site), __package__)
        return module.ComicBook()
