import json

from flask import (
    Blueprint,
    jsonify,
    request,
    abort
)
from flask_login import login_required
from onepiece.exceptions import ComicbookException


from . import task
from ..common import handle_404
from ..common import crawler

manage_app = Blueprint("manage", __name__, url_prefix='/manage')
manage_app.register_error_handler(ComicbookException, handle_404)


@manage_app.route("/cookies/<site>", methods=['GET'])
@login_required
def get_cookies(site):
    cookies = crawler.get_cookies(site=site)
    return jsonify(dict(cookies=cookies))


@manage_app.route("/cookies/<site>", methods=['POST'])
@login_required
def update_cookies(site):
    content = request.json or {}
    cookies = content.get('cookies')
    cover = content.get('cover', False)
    if not cookies or not isinstance(cookies, list):
        abort(400)
    ret = crawler.update_cookies(site=site, cookies=cookies, cover=cover)
    return jsonify(dict(cookies=ret))


@manage_app.route("/task/add")
@login_required
def add_task():
    site = request.args.get('site')
    comicid = request.args.get('comicid')
    params = request.args.get('params')
    params = json.loads(params) if params else {}
    keys = ['ext_name', 'chapters', 'is_download_all', 'is_gen_pdf', 'is_gen_zip',
            'is_single_image', 'quality', 'receivers', 'is_send_mail']
    clean_params = {}
    for k in keys:
        if k in params:
            value = params[k]
            if isinstance(value, (bool, int, str)):
                clean_params[k] = value
    result = task.add_task(site=site,
                           comicid=comicid,
                           params=clean_params)
    return jsonify(dict(data=result))


@manage_app.route("/task/list")
@login_required
def list_task():
    page = request.args.get('page', default=1, type=int)
    size = 20
    result = task.list_task(page=page, size=size)
    return jsonify(dict(list=result))


@manage_app.route("/proxy/<site>", methods=['GET'])
@login_required
def get_proxy(site):
    if 'proxy' in request.args:
        proxy = request.args.get('proxy') or None
        crawler.set_proxy(site=site, proxy=proxy)
    return jsonify(proxy=crawler.get_proxy(site=site))
