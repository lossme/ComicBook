import datetime
import logging
from flask import (
    Blueprint,
    jsonify,
    request,
    abort,
    current_app
)
import cachetools.func

from onepiece.comicbook import ComicBook
from onepiece.exceptions import (
    ComicbookException,
    NotFoundError,
    SiteNotSupport
)


logger = logging.getLogger(__name__)
app = Blueprint("api", __name__, url_prefix='/api')
CACHE_TIME = 600


@app.errorhandler(ComicbookException)
def handle_404(error):
    if isinstance(error, NotFoundError):
        return jsonify(
            {
                "message": str(error)
            }), 404
    elif isinstance(error, SiteNotSupport):
        return jsonify(
            {
                "message": str(error)
            }), 400
    else:
        return jsonify(
            {
                "message": str(error)
            }), 500


@cachetools.func.ttl_cache(maxsize=1024, ttl=CACHE_TIME, typed=False)
def get_comicbook_from_cache(site, comicid):
    comicbook = ComicBook.create_comicbook(site=site, comicid=comicid)
    proxy_config = current_app.config.get('CRAWLER_PROXY', {})
    proxy = proxy_config.get(site)
    if proxy:
        comicbook.crawler.get_session().set_proxy(proxy)
    return comicbook


def comicbook_update_check(comicbook, cache_time=CACHE_TIME, force_refresh=False):
    if force_refresh \
            or not comicbook.crawler_time \
            or (datetime.datetime.now() - comicbook.crawler_time).total_seconds() > cache_time:
        comicbook.start_crawler()
    return comicbook


@app.route("/<site>/comic/<comicid>")
def get_comicbook_info(site, comicid):
    force_refresh = request.args.get('force_refresh') or ''
    force_refresh = force_refresh.lower() == 'true'
    comicbook = get_comicbook_from_cache(site=site, comicid=comicid)
    comicbook_update_check(comicbook, force_refresh=force_refresh)
    return jsonify(comicbook.to_dict())


@app.route("/<site>/comic/<comicid>/<int:chapter_number>")
def get_chapter_info(site, comicid, chapter_number):
    force_refresh = request.args.get('force_refresh') or ''
    force_refresh = force_refresh.lower() == 'true'
    comicbook = get_comicbook_from_cache(site, comicid)
    comicbook_update_check(comicbook, force_refresh=force_refresh)
    chapter = comicbook.Chapter(chapter_number, force_refresh=force_refresh)
    return jsonify(chapter.to_dict())


@app.route("/<site>/search")
def search(site):
    name = request.args.get('name')
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=None, type=int)
    if not name:
        abort(400)
    comicbook = get_comicbook_from_cache(site, comicid=None)
    result = comicbook.search(name=name, page=page, limit=limit)
    return jsonify(
        {
            "search_result": result.to_dict()
        }
    )


@app.route("/<site>/tags")
def tags(site):
    comicbook = get_comicbook_from_cache(site, comicid=None)
    tags = comicbook.get_tags()
    return jsonify(
        {
            "tags": tags.to_dict()
        }
    )


@app.route("/<site>/list")
def tag_list(site):
    tag = request.args.get('tag')
    page = request.args.get('page', default=1, type=int)
    comicbook = get_comicbook_from_cache(site, comicid=None)
    result = comicbook.get_tag_result(tag=tag, page=page)
    return jsonify(
        {
            "list": result.to_dict()
        }
    )


@app.route("/<site>/latest")
def latest(site):
    page = request.args.get('page', default=1, type=int)
    comicbook = get_comicbook_from_cache(site, comicid=None)
    latest = comicbook.latest(page=page)
    return jsonify(
        {
            "latest": [item.to_dict() for item in latest]
        }
    )
