# TencentComicBook

## 腾讯漫画、鼠绘漫画爬虫

### 本项目特点

- [x] 漫画批量下载或全集下载
- [x] 分目录保存
- [x] 支持鼠绘漫画、腾讯漫画
- [x] 支持生成pdf
- [x] 支持发送到邮箱

### 安装依赖

若只是下载图片，只需安装`requests`即可食用

`python3 -m pip install requests`

若要生成pdf和发送到邮箱，则需要安装完整依赖

`python3 -m pip install -r requirements.txt`

**注意**: 发送到邮箱需预先配置好信息

复制`onepiece/config.example.py`并命名为`onepiece/config.py`，并根据实际情况修改`onepiece/config.py`的参数

### 常规使用

默认从腾讯漫画下载，注意鼠绘漫画和腾讯漫画的id区别

- 下载海贼王最新一集: `python3 -m onepiece`
- 下载漫画 id=505430 最新一集: `python3 -m onepiece -id=505430`
- 下载漫画 id=505430 所有章节: `python3 -m onepiece -id=505430 --all`
- 下载漫画 id=505430 第800集: `python3 -m onepiece -id=505430 -c=800`
- 下载漫画 id=505430 倒数第二集: `python3 -m onepiece -id=505430 -c=-2`
- 下载漫画 id=505430 1到5集,7集，9到10集: `python3 -m onepiece -id=505430 -i=1-5,7,9-10`
- 下载漫画 id=505430 800集至最新一集: `python3 -m onepiece -id=505430 -i=800-9999`
- 从鼠绘漫画下载海贼王最新一集: `python3 -m onepiece --site=ishuhui -id=1`
- 下载漫画并生成pdf文件: `python3 -m onepiece --site=ishuhui -id=1 --pdf`
- 下载漫画并推送到邮箱: `python3 -m onepiece --site=ishuhui -id=1 --pdf --mail`


### 使用帮助

```
>>> python -m onepiece --help

usage: __main__.py [-h] [-id COMICID] [-i INTERVAL] [-c CHAPTER] [-t THREAD]
                   [--all] [--pdf] [--mail] [-o OUTPUT] [--site {qq,ishuhui}]

optional arguments:
  -h, --help            show this help message and exit
  -id COMICID, --comicid COMICID
                        漫画id，海贼王: 505430
                        (http://ac.qq.com/Comic/ComicInfo/id/505430)
  -i INTERVAL, --interval INTERVAL
                        要下载的章节区间, 如 -i 1-5,7,9-10
  -c CHAPTER, --chapter CHAPTER
                        要下载的章节chapter，默认下载最新章节。如 -c 666
  -t THREAD, --thread THREAD
                        线程池数,默认开启8个线程池,下载多个章节时效果才明显
  --all                 若设置了则下载该漫画的所有章节, 如 --all
  --pdf                 若设置了则生成pdf文件, 如 --pdf
  --mail                若设置了则发送到邮箱, 如 --mail。需要预先创建配置文件。可以参照onepiece/config.example.py
                        /config.py文件
  -o OUTPUT, --output OUTPUT
                        文件保存路径，默认保存在当前路径下的download文件夹
  --site {qq,ishuhui}   网站：支持qq，ishuhui

```

**免责声明**：本项目仅供学习交流之用，请勿用于非法用途。
