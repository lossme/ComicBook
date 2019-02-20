from flask import Blueprint, jsonify
import cachetools.func

from onepiece.comicbook import ComicBook
from onepiece.exceptions import NotFoundError


app = Blueprint("main", __name__, url_prefix="/api")


@app.errorhandler(NotFoundError)
def handle_404(error):
    return jsonify(
        {
            "message": "资源未找到"
        }), 404


@cachetools.func.ttl_cache(maxsize=1024, ttl=3600, typed=False)
def get_comicbook(site, comicid):
    return ComicBook.create_comicbook(site=site, comicid=comicid)


@cachetools.func.ttl_cache(maxsize=1024, ttl=3600 * 24, typed=False)
def get_chapter(site, comicid, chapter_number):
    comicbook = get_comicbook(site, comicid)
    return comicbook.Chapter(chapter_number)


@app.route("/<site>/<comicid>")
def get_comicbook_info(site, comicid):
    comicbook = get_comicbook(site=site, comicid=comicid)

    return jsonify(
        {
            "name": comicbook.name,
            "desc": comicbook.desc,
            "source_name": comicbook.source_name,
            "max_chapter_number": comicbook.max_chapter_number
        }
    )


@app.route("/<site>/<comicid>/<int:chapter_number>")
def get_chapter_info(site, comicid, chapter_number):
    chapter = get_chapter(site=site, comicid=comicid, chapter_number=chapter_number)
    return jsonify(
        {
            "name": chapter.comicbook.name,
            "desc": chapter.comicbook.desc,
            "source_name": chapter.comicbook.source_name,
            "max_chapter_number": chapter.comicbook.max_chapter_number,
            "chapter_number": chapter_number,
            "chapter_title": chapter.title,
            "image_urls": chapter.image_urls
        }
    )
