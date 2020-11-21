import json
import pickle

import requests

from .utils import ensure_file_dir_exists

requests.packages.urllib3.disable_warnings()


class SessionMgr(object):
    SESSION_INSTANCE = {}
    DEFAULT_HEADERS = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36')
    }
    COOKIES_KEYS = ['name', 'value', 'path', 'domain', 'secure']
    DEFAULT_VERIFY = False

    @classmethod
    def get_session(cls, site):
        if site not in cls.SESSION_INSTANCE:
            session = requests.Session()
            session.headers.update(cls.DEFAULT_HEADERS)
            session.verify = cls.DEFAULT_VERIFY
            cls.SESSION_INSTANCE[site] = session
        return cls.SESSION_INSTANCE[site]

    @classmethod
    def set_session(cls, site, session):
        cls.SESSION_INSTANCE[site] = session
        return session

    @classmethod
    def load_session(cls, site, path):
        with open(path, "rb") as f:
            session = pickle.load(f)
            assert isinstance(session, requests.Session)
            cls.set_session(site, session)
            return session

    @classmethod
    def export_session(cls, site, path):
        ensure_file_dir_exists(path)
        session = cls.get_session(site)
        with open(path, "wb") as f:
            pickle.dump(session, f)

    @classmethod
    def update_cookies(cls, site, cookies):
        session = cls.get_session(site=site)
        for cookie in cookies:
            data = {key: cookie.get(key) for key in cls.COOKIES_KEYS}
            session.cookies.set(**data)

    @classmethod
    def load_cookies(cls, site, path):
        with open(path) as f:
            cookies = json.load(f)
            cls.update_cookies(site=site, cookies=cookies)
        return cls.get_session(site=site)

    @classmethod
    def export_cookies(cls, site, path):
        cookies = cls.get_cookies(site)
        ensure_file_dir_exists(path)
        with open(path, 'w') as f:
            json.dump(cookies, f, indent=4)

    @classmethod
    def get_cookies(cls, site):
        cookies = []
        session = cls.get_session(site=site)
        for c in session.cookies:
            args = dict(vars(c).items())
            data = {key: args.get(key) for key in cls.COOKIES_KEYS}
            cookies.append(data)
        return cookies

    @classmethod
    def clear_cookies(cls, site):
        session = cls.get_session(site=site)
        session.cookies.clear_session_cookies()

    @classmethod
    def set_proxy(cls, site, proxy):
        session = cls.get_session(site)
        session.proxies = {
            'http': proxy,
            'https': proxy
        }

    @classmethod
    def get_proxy(cls, site):
        session = cls.get_session(site)
        return session.proxies.get('http')

    @classmethod
    def set_verify(cls, site, verify):
        session = cls.get_session(site)
        session.verify = verify
