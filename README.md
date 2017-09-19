# TencentComicBook
## 腾讯漫画批量抓取


#### 安装依赖

`pip install -r requirements.txt`


#### 使用帮助
```
python3 onepiece.py --help
Usage: onepiece.py [OPTIONS] [MODE]...

  根据腾讯漫画id下载图片,默认下载海贼王最新一集。

  下载海贼王最新一集: python3 onepiece.py

  下载漫画 id=505430 所有章节: python3 onepiece.py -id 505430 all

  下载漫画 id=505430 第800集: python3 onepiece.py -id 505430 -c 800

  下载漫画 id=505430 倒数第二集: python3 onepiece.py -id 505430 -c -2

  下载漫画 id=505430 1到5集,7集，9到10集: python3 onepiece.py -id 505430 -i 1-5,7,9-10

Options:
  -id, --id INTEGER      漫画id，海贼王: 505430
                         (http://ac.qq.com/Comic/ComicInfo/id/505430)
  -i, --interval TEXT    要下载的章节区间, 如 -i 1-5,7,9-10
  -c, --chapter INTEGER  要下载的章节chapter，默认下载最新章节。如 -c 666
  -t, --thread INTEGER   线程池数,默认开启8个线程池,下载多个章节时效果才明显
  --help                 Show this message and exit.

'''
