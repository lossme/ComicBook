import logging
import os
import datetime

from flask import current_app, abort

from onepiece.utils import parser_chapter_str
from onepiece.utils.mail import Mail

from .model import (
    CrawlerTask,
    TaskStatus
)
from . import db
from . import const
from .common import (
    run_in_background,
    log_exception
)

from . import crawler


logger = logging.getLogger(__name__)


def check_task_secret(secret):
    right_secret = current_app.config.get("TASK_SECRET")
    if right_secret:
        if secret != right_secret:
            abort(403)


def add_task(site, comicid, chapter, is_all, send_mail, gen_pdf, receivers):
    hash_code = CrawlerTask.gen_hash(site=site,
                                     comicid=comicid,
                                     chapter=chapter,
                                     is_all=is_all,
                                     send_mail=send_mail,
                                     gen_pdf=gen_pdf,
                                     receivers=receivers)

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
                       chapter=chapter,
                       is_all=is_all,
                       send_mail=send_mail,
                       gen_pdf=gen_pdf,
                       receivers=receivers,
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
        db.session.flush()
        db.session.commit()

        comicbook = crawler.get_comicbook_from_cache(site=task.site, comicid=task.comicid)
        comicbook.start_crawler()

        is_all = task.is_all == 1
        chapter_str = task.chapter
        is_send_mail = task.send_mail == 1
        is_gen_pdf = task.gen_pdf == 1
        output_dir = app.config['DATA_DIR']
        name = comicbook.name
        last_chapter_number = comicbook.last_chapter_number

        chapter_number_list = parser_chapter_str(chapter_str=chapter_str,
                                                 last_chapter_number=last_chapter_number,
                                                 is_all=is_all)

        for chapter_number in chapter_number_list:
            try:
                chapter = comicbook.Chapter(chapter_number)
                chapter_number = chapter.chapter_number
                title = chapter.title
                logger.info(f"downloading [{name}] {chapter_number} [{title}]")
                if is_gen_pdf or is_send_mail:
                    pdf_path = chapter.save_as_pdf(output_dir=output_dir)
                    receivers = None
                    if task.receivers:
                        receivers = task.receivers.split(',')
                    logger.info("gen pdf success. task_id=%s pdf_path=%s", task_id, pdf_path)
                    if is_send_mail:
                        mail_config = app.config['MAIL_CONFIG']
                        mail = Mail(**mail_config)
                        subject = os.path.basename(pdf_path)
                        mail.send(subject=subject, file_list=[pdf_path, ], receivers=receivers)
                else:
                    chapter_dir = chapter.save(output_dir=output_dir)
                    logger.info("download success. task_id=%s chapter_dir=%s", task_id, chapter_dir)
            except Exception as e:
                logger.exception('task error. task_id=%s', task_id)
                task.reason = str(e)

        task.cost_time = int((datetime.datetime.utcnow() - task.start_time).total_seconds())
        task.status = TaskStatus.DONE
        db.session.flush()
        db.session.commit()


def list_task(page, size):
    offset = (page - 1) * size
    res = db.session.query(CrawlerTask)\
        .order_by(CrawlerTask.id.desc())\
        .offset(offset)\
        .limit(size)
    return [i.to_dict() for i in res]
