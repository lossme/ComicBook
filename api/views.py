from flask import (
    jsonify,
    current_app,
    Blueprint,
    request
)
from onepiece.comicbook import ComicBook

from . import const
from .const import ConfigKey


app = Blueprint("index", __name__, url_prefix='/',)


@app.route("/")
def index():
    prefix = current_app.config.get(ConfigKey.URL_PREFIX, '')
    q_site = request.args.get('site')
    examples = []
    if q_site:
        items = []
        if q_site in ComicBook.CRAWLER_CLS_MAP:
            items.append((q_site, ComicBook.CRAWLER_CLS_MAP[q_site]))
    else:
        items = ComicBook.CRAWLER_CLS_MAP.items()
    for site, crawler in items:
        if site in const.NOT_SUPPORT_SITES:
            continue
        item = dict(
            site=site,
            source_name=crawler.SOURCE_NAME,
            source_index=crawler.SITE_INDEX,
            r18=crawler.R18,
            examples=[])
        examples.append(item)

        site_examples = item['examples']
        comicid = crawler.DEFAULT_COMICID
        search_name = crawler.DEFAULT_SEARCH_NAME
        tag = crawler.DEFAULT_TAG

        site_examples.append(dict(
            desc='根据漫画id 获取漫画信息',
            api=prefix + f'/api/{site}/comic/{comicid}'
        ))

        # 章节详情
        site_examples.append(dict(
            desc='获取章节信息',
            api=prefix + f'/api/{site}/comic/{comicid}/1'
        ))

        # 搜索
        site_examples.append(dict(
            desc='搜索',
            api=prefix + f'/api/{site}/search?name={search_name}&page=1'
        ))

        # 最近更新
        site_examples.append(dict(
            desc="查看站点最近更新",
            api=prefix + f'/api/{site}/latest?page=1'
        ))

        # 查看所有tags
        site_examples.append(dict(
            desc="获取站点所有tags",
            api=prefix + f'/api/{site}/tags'
        ))

        # 根据tag查询
        site_examples.append(dict(
            desc="根据tag查询",
            api=prefix + f'/api/{site}/list?tag={tag}&page=1'
        ))

    aggregate_examples = []
    aggregate_examples.append(dict(
        desc="聚合搜索",
        api=prefix + '/aggregate/search?name=海贼&site=bilibili,u17'
    ))

    manage_examples = []
    manage_examples.append(dict(
        desc='添加任务',
        api=prefix + '/manage/task/add?site=qq&comicid=505430&chapter=-1&gen_pdf=1&send_mail=0',
    ))
    manage_examples.append(dict(
        desc='查看任务',
        api=prefix + '/manage/task/list?page=1',
    ))
    # GET获取/POST更新站点cookies
    manage_examples.append(dict(
        desc='GET获取/POST更新站点cookies',
        api=prefix + f'/manage/cookies/qq',
    ))
    # 查看/设置站点代理
    manage_examples.append(dict(
        desc='查看/设置站点代理',
        api=prefix + f'/manage/proxy/qq',
    ))

    return jsonify(
        {
            "api_examples": examples,
            "aggregate_examples": aggregate_examples,
            "manage_examples": manage_examples
        }
    )
