import json
import pickle

import requests

from .utils import ensure_file_dir_exists

requests.packages.urllib3.disable_warnings()


class Session(requests.Session):
    DEFAULT_HEADERS = {
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/65.0.3325.146 Safari/537.36')
    }
    TIMEOUT = 30
    COOKIES_KEYS = ['name', 'value', 'path', 'domain', 'secure']

    def export(self, path):
        ensure_file_dir_exists(path)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path):
        with open(path, "rb") as f:
            session = pickle.load(f)
            assert isinstance(session, cls)
            return session

    def load_cookies(self, cookies_path):
        with open(cookies_path) as f:
            cookies = json.load(f)
            self._update_cookies(cookies)
        return self

    def export_cookies(self, cookies_path):
        cookies = self._get_cookies()
        ensure_file_dir_exists(cookies_path)
        with open(cookies_path, 'w') as f:
            json.dump(cookies, f, indent=4)

    def _update_cookies(self, cookies):
        for cookie in cookies:
            data = {key: cookie.get(key) for key in self.COOKIES_KEYS}
            self.cookies.set(**data)

    def clear_cookies(self):
        self.cookies.clear_session_cookies()

    def _get_cookies(self):
        cookies = []
        for c in self.cookies:
            args = dict(vars(c).items())
            data = {key: args.get(key) for key in self.COOKIES_KEYS}
            cookies.append(data)
        return cookies

    def set_proxy(self, proxy):
        self.proxies = {
            'http': proxy,
            'https': proxy
        }

    @classmethod
    def create_session(cls):
        session = cls()
        session.headers.update(session.DEFAULT_HEADERS)
        return session
