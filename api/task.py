import logging
import datetime
import json

from flask import current_app

from onepiece.utils.mail import Mail
from .model import (
    CrawlerTask,
    TaskStatus
)
from . import db
from . import const
from .const import ConfigKey
from .common import (
    run_in_background,
    log_exception
)

from . import crawler
from onepiece.cli import download_main

logger = logging.getLogger(__name__)


def add_task(site, comicid, params):
    params = json.dumps(params, sort_keys=True)
    hash_code = CrawlerTask.gen_hash(site=site, comicid=comicid, params=params)

    task = db.session.query(CrawlerTask)\
        .filter(CrawlerTask.hash_code == hash_code)\
        .order_by(CrawlerTask.create_time.desc()).first()
    pre_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=const.TASK_AVOID_REPEAT_TIME)
    if task and task.create_time >= pre_time:
        return task.to_dict()

    crawler.check_site_support(site)
    comicbook = crawler.get_comicbook_from_cache(site=site, comicid=comicid)
    comicbook.start_crawler()

    task = CrawlerTask(site=site,
                       comicid=comicid,
                       name=comicbook.name,
                       source_url=comicbook.source_url,
                       params=params,
                       status=TaskStatus.INIT,
                       hash_code=hash_code)
    db.session.add(task)
    db.session.flush()
    task_id = task.id
    db.session.commit()
    app = current_app._get_current_object()
    run_in_background(func=run_task, app=app, task_id=task_id)
    # run_task(app=app, task_id=task_id)
    return task.to_dict()


@log_exception
def run_task(app, task_id):
    logger.info('run_task. task_id=%s', task_id)
    with app.app_context():
        task = db.session.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
        if not task:
            logger.info('task not found. task_id=%s', task_id)
            return

        if task.status in TaskStatus.DONE_STATUS:
            logger.info('task already done. task_id=%s', task_id)
            return
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.datetime.utcnow()
        db.session.commit()

        comicbook = crawler.get_comicbook_from_cache(site=task.site, comicid=task.comicid)
        comicbook.start_crawler()

        mail_config = app.config['MAIL_CONFIG']
        mail = Mail(**mail_config)
        params = json.loads(task.params)
        download_main(comicbook=comicbook,
                      output_dir=app.config[ConfigKey.DOWNLOAD_DIR],
                      mail=mail, **params)
        task.cost_time = int((datetime.datetime.utcnow() - task.start_time).total_seconds())
        task.status = TaskStatus.DONE
        db.session.commit()


def list_task(page, size):
    offset = (page - 1) * size
    res = db.session.query(CrawlerTask)\
        .order_by(CrawlerTask.id.desc())\
        .offset(offset)\
        .limit(size)
    return [i.to_dict() for i in res]
