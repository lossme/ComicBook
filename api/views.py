import logging
from flask import (
    Blueprint,
    jsonify,
    request,
    abort,
    current_app
)
import cachetools.func
from concurrent.futures import ThreadPoolExecutor

from onepiece.comicbook import ComicBook
from onepiece.exceptions import (
    ComicbookException,
    NotFoundError,
    SiteNotSupport
)


logger = logging.getLogger(__name__)
app = Blueprint("api", __name__, url_prefix='/api')
aggregate_app = Blueprint("aggregate", __name__, url_prefix='/aggregate')

CACHE_TIME = 600
THREAD_POOL = None
POOL_SIZE = 4


def get_pool():
    global THREAD_POOL
    if THREAD_POOL is None:
        pool_size = current_app.config['POOL_SIZE']
        THREAD_POOL = ThreadPoolExecutor(max_workers=pool_size)
    return THREAD_POOL


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
def get_comicbook_from_cache(site, comicid=None):
    comicbook = ComicBook.create_comicbook(site=site, comicid=comicid)
    proxy_config = current_app.config.get('CRAWLER_PROXY', {})
    proxy = proxy_config.get(site)
    if proxy:
        comicbook.crawler.get_session().set_proxy(proxy)
    return comicbook


@app.route("/<site>/comic/<comicid>")
def get_comicbook_info(site, comicid):
    comicbook = get_comicbook_from_cache(site=site, comicid=comicid)
    return jsonify(comicbook.to_dict())


@app.route("/<site>/comic/<comicid>/<int:chapter_number>")
def get_chapter_info(site, comicid, chapter_number):
    comicbook = get_comicbook_from_cache(site, comicid)
    chapter = comicbook.Chapter(chapter_number)
    return jsonify(chapter.to_dict())


@app.route("/<site>/search")
def search(site):
    name = request.args.get('name')
    page = request.args.get('page', default=1, type=int)
    if not name:
        abort(400)
    comicbook = get_comicbook_from_cache(site, comicid=None)
    result = comicbook.search(name=name, page=page)
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
    result = comicbook.latest(page=page)
    return jsonify(
        {
            "latest": result.to_dict()
        }
    )


@aggregate_app.route("/search")
def aggregate_search():
    site = request.args.get('site')
    name = request.args.get('name')
    if site:
        sites = []
        for s in set(site.split(',')):
            if s in ComicBook.CRAWLER_CLS_MAP:
                sites.append(s)
    else:
        sites = list(ComicBook.CRAWLER_CLS_MAP.keys())
    if not name:
        abort(400)
    ret = []
    pool = get_pool()
    future_list = []
    for site in sites:
        comicbook = get_comicbook_from_cache(site=site)
        future = pool.submit(comicbook.search, name=name)
        future_list.append(future)
    for future in future_list:
        try:
            for i in future.result():
                ret.append(i.to_dict())
        except Exception:
            logger.exception('task error. future=%s future._exception=%s', future, future._exception)
    return jsonify(
        {
            "list": ret
        }
    )
