class Config(object):
    DEBUG = False
    JSON_AS_ASCII = False
    LOG_LEVEL = 'INFO'
    CRAWLER_PROXY = {}
    POOL_SIZE = 8


class ProductionConfig(Config):
    URL_PREFIX = "http://127.0.0.1:8000"
    DEFAULT_PROXY = 'socks5://127.0.0.1:1080'

    # 指定哪些站点走代理 可参考 DevelopmentConfig
    CRAWLER_PROXY = {}


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    URL_PREFIX = "http://127.0.0.1:8000"
    DEFAULT_PROXY = 'socks5://127.0.0.1:1082'

    CRAWLER_PROXY = {
        '18comic': DEFAULT_PROXY,
        'manhuagui': DEFAULT_PROXY,
        'nhentai': DEFAULT_PROXY,
        'wnacg': DEFAULT_PROXY,
    }
