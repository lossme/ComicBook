import logging
from flask import (
    Blueprint,
    jsonify,
    request,
    abort
)

from onepiece.exceptions import ComicbookException
from . import crawler
from .common import handle_404

logger = logging.getLogger(__name__)
app = Blueprint("api", __name__, url_prefix='/api')
aggregate_app = Blueprint("aggregate", __name__, url_prefix='/aggregate')

app.register_error_handler(ComicbookException, handle_404)
aggregate_app.register_error_handler(ComicbookException, handle_404)


@app.route("/<site>/comic/<comicid>")
def get_comicbook_info(site, comicid):
    result = crawler.get_comicbook_info(site=site, comicid=comicid)
    return jsonify(result)


@app.route("/<site>/comic/<comicid>/<int:chapter_number>")
def get_chapter_info(site, comicid, chapter_number):
    result = crawler.get_chapter_info(site=site, comicid=comicid, chapter_number=chapter_number)
    return jsonify(result)


@app.route("/<site>/search")
def search(site):
    name = request.args.get('name')
    page = request.args.get('page', default=1, type=int)
    if not name:
        abort(400)
    result = crawler.get_search_resuult(site=site, name=name, page=page)
    return jsonify(dict(search_result=result))


@app.route("/<site>/tags")
def tags(site):
    result = crawler.get_tags(site)
    return jsonify(dict(tags=result))


@app.route("/<site>/list")
def tag_list(site):
    tag = request.args.get('tag')
    page = request.args.get('page', default=1, type=int)
    result = crawler.get_tag_result(site=site, tag=tag, page=page)
    return jsonify(dict(list=result))


@app.route("/<site>/latest")
def latest(site):
    page = request.args.get('page', default=1, type=int)
    result = crawler.get_latest(site=site, page=page)
    return jsonify(dict(latest=result))


@aggregate_app.route("/search")
def aggregate_search():
    site = request.args.get('site')
    name = request.args.get('name')
    if not name:
        abort(400)
    result = crawler.aggregate_search(site=site, name=name)
    return jsonify(dict(list=result))
