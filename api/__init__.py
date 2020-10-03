from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False
    app.url_map.strict_slashes = False

    from .views import app as main_app
    app.register_blueprint(main_app)
    app.add_url_rule('/', 'index', index)

    return app


def index():
    from onepiece.comicbook import ComicBook
    example = []
    for site, crawler in ComicBook.CRAWLER_CLS_MAP.items():
        example.append('/api/{site}?name={name}'.format(
            site=site, name=crawler.DEFAULT_COMIC_NAME))
        example.append('/api/{site}/{comicid}'.format(
            site=site, comicid=crawler.DEFAULT_COMICID))
        example.append('/api/{site}/{comicid}/1'.format(
            site=site, comicid=crawler.DEFAULT_COMICID))
    return jsonify(
        {
            "api_status": "ok",
            "example": example
        }
    )
