from flask import Blueprint, jsonify
import cachetools.func

from onepiece.comicbook import ComicBook
from onepiece.exceptions import NotFoundError


app = Blueprint("main", __name__, url_prefix="/api")


@app.errorhandler(NotFoundError)
def handle_404(error):
    return jsonify(
        {
            "message": str(error)
        }), 404


@cachetools.func.ttl_cache(maxsize=1024, ttl=3600, typed=False)
def get_comicbook(site, comicid):
    return ComicBook.create_comicbook(site=site, comicid=comicid)


@cachetools.func.ttl_cache(maxsize=1024, ttl=3600 * 24, typed=False)
def get_comicbook_and_chapter(site, comicid, chapter_number):
    comicbook = get_comicbook(site, comicid)
    return comicbook, comicbook.Chapter(chapter_number)


@app.route("/<site>/<comicid>")
def get_comicbook_info(site, comicid):
    comicbook = get_comicbook(site=site, comicid=comicid)
    return jsonify(comicbook.to_dict())


@app.route("/<site>/<comicid>/<int:chapter_number>")
def get_chapter_info(site, comicid, chapter_number):
    comicbook, chapter = get_comicbook_and_chapter(site=site, comicid=comicid, chapter_number=chapter_number)
    rv = comicbook.to_dict()
    rv["chapter"] = chapter.to_dict()
    return jsonify(rv)
