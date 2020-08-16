import pickle

import requests

requests.packages.urllib3.disable_warnings()


class Session(requests.Session):
    DEFAULT_HEADERS = {
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/65.0.3325.146 Safari/537.36')
    }
    TIMEOUT = 30

    def export(self, path):
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path):
        with open(path, "rb") as f:
            session = pickle.load(f)
            assert isinstance(session, cls)
            return session


default_session = Session()
default_session.headers.update(default_session.DEFAULT_HEADERS)
