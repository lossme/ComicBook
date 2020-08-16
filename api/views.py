import datetime
from flask import (
    Blueprint,
    jsonify,
    request,
    abort
)
import cachetools.func

from onepiece.comicbook import ComicBook
from onepiece.exceptions import (
    ComicbookException,
    NotFoundError,
    SiteNotSupport
)


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
    return comicbook


def comicbook_update_check(comicbook, cache_time=CACHE_TIME, force_refresh=False):
    if force_refresh \
            or not comicbook.crawler_time \
            or (datetime.datetime.now() - comicbook.crawler_time).total_seconds() > cache_time:
        comicbook.start_crawler()
    return comicbook


@app.route("/<site>")
def search(site):
    name = request.args.get('name')
    limit = request.args.get('limit', default=20, type=int)
    if not name:
        abort(400)
    comicbook = get_comicbook_from_cache(site, comicid=None)
    search_result_item_list = comicbook.search(site=site, name=name, limit=limit)
    return jsonify(
        {
            "search_result": [item.to_dict() for item in search_result_item_list]
        }
    )


@app.route("/<site>/<comicid>")
def get_comicbook_info(site, comicid):
    force_refresh = request.args.get('force_refresh') or ''
    force_refresh = force_refresh.lower() == 'true'
    comicbook = get_comicbook_from_cache(site=site, comicid=comicid)
    comicbook_update_check(comicbook, force_refresh=force_refresh)
    return jsonify(comicbook.to_dict())


@app.route("/<site>/<comicid>/<int:chapter_number>")
def get_chapter_info(site, comicid, chapter_number):
    force_refresh = request.args.get('force_refresh') or ''
    force_refresh = force_refresh.lower() == 'true'
    comicbook = get_comicbook_from_cache(site, comicid)
    comicbook_update_check(comicbook, force_refresh=force_refresh)
    chapter = comicbook.Chapter(chapter_number, force_refresh=force_refresh)
    return jsonify(chapter.to_dict())
