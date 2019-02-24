from flask import Blueprint, jsonify, request, abort
import cachetools.func

from onepiece.comicbook import ComicBook
from onepiece.exceptions import NotFoundError


app = Blueprint("main", __name__)


@app.errorhandler(NotFoundError)
def handle_404(error):
    return jsonify(
        {
            "message": str(error)
        }), 404


@cachetools.func.ttl_cache(maxsize=1024, ttl=3600, typed=False)
def get_comicbook(site, comicid):
    return ComicBook.create_comicbook(site=site, comicid=comicid)


@app.route("/comic/<site>/<comicid>")
def get_comicbook_info(site, comicid):
    comicbook = get_comicbook(site=site, comicid=comicid)
    return jsonify(comicbook.to_dict())


@app.route("/comic/<site>/<comicid>/<int:chapter_number>")
def get_chapter_info(site, comicid, chapter_number):
    comicbook = get_comicbook(site, comicid)
    chapter = comicbook.Chapter(chapter_number)
    rv = comicbook.to_dict()
    rv["chapter"] = chapter.to_dict()
    return jsonify(rv)


@app.route("/search/<site>")
def search(site):
    name = request.args.get('name')
    if not name:
        abort(400)
    search_result_item_list = ComicBook.search(site=site, name=name)
    return jsonify(
        {
            "search_result": [item.to_dict() for item in search_result_item_list]
        }
    )
