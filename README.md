# TencentComicBook
## 腾讯漫画批量抓取


### 安装依赖

`python3 -m pip install -r requirements.txt`


### 常规使用
- 下载海贼王最新一集: python3 onepiece.py
- 下载漫画 id=505430 最新一集: python3 onepiece.py -id 505430
- 下载漫画 id=505430 所有章节: python3 onepiece.py -id 505430 -m all
- 下载漫画 id=505430 第800集: python3 onepiece.py -id 505430 -c 800
- 下载漫画 id=505430 倒数第二集: python3 onepiece.py -id 505430 -c -2
- 下载漫画 id=505430 1到5集,7集，9到10集: python3 onepiece.py -id 505430 -i 1-5,7,9-10
- 下载漫画 id=505430 800集至最新一集: python3 onepiece.py -id 505430 -i 800-9999

### 使用帮助


```
>>>python3 onepiece.py --help

usage: onepiece.py [-h] [-id COMIC_ID] [-i INTERVAL] [-c CHAPTER] [-t THREAD]
                   [-m MODE]

optional arguments:
  -h, --help            show this help message and exit
  -id COMIC_ID, --comic_id COMIC_ID
                        漫画id，海贼王: 505430
                        (http://ac.qq.com/Comic/ComicInfo/id/505430)
  -i INTERVAL, --interval INTERVAL
                        要下载的章节区间, 如 -i 1-5,7,9-10
  -c CHAPTER, --chapter CHAPTER
                        要下载的章节chapter，默认下载最新章节。如 -c 666
  -t THREAD, --thread THREAD
                        线程池数,默认开启8个线程池,下载多个章节时效果才明显
  -m MODE, --mode MODE  下载模式，若为 a/all 则下载该漫画的所有章节, 如 -m all

```
