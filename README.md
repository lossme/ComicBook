# TencentComicBook
腾讯漫画批量抓取

'''
>>>python3 onepiece.py --help
Usage: onepiece.py [OPTIONS]

  根据腾讯漫画id下载图片

Options:
  --id INTEGER  请输入你想要下载的漫画的id,默认下载海贼王
                如海贼王http://ac.qq.com/Comic/ComicInfo/id/505430的id为505430:
  --s TEXT      下载多个章节,输入章节区间,如 --s 1-10,25,30-40
  --c INTEGER   输入要下载的章节chapter，默认下载最新章节
                如倒数第二 --c -2
  --t INTEGER   线程池数,默认开启8个线程池,下载多个章节时效果才明显
  --help        Show this message and exit.
'''
