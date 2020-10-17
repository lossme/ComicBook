class Config(object):
    DEBUG = False
    JSON_AS_ASCII = False
    LOG_LEVEL = 'INFO'

    URL_PREFIX = "http://127.0.0.1:5000"
    DEFAULT_PROXY = 'socks5://127.0.0.1:1082'

    CRAWLER_PROXY = {
        '18comic': DEFAULT_PROXY,
        'manhuagui': DEFAULT_PROXY,
        'nhentai': DEFAULT_PROXY,
        'wnacg': DEFAULT_PROXY,
    }


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'DEBUG'


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
