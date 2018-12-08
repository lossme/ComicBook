# TencentComicBook

腾讯漫画、鼠绘漫画爬虫

## 本项目特点

- [x] 漫画批量下载或全集下载
- [x] 分目录保存
- [x] 支持鼠绘漫画、腾讯漫画
- [x] 支持生成pdf
- [x] 支持发送到邮箱

## 安装依赖

若只是下载图片，只需安装`requests`即可食用

`python3 -m pip install requests`

若要生成pdf和发送到邮箱，则需要安装完整依赖

`python3 -m pip install -r requirements.txt`

**注意**: 发送到邮箱需预先配置好信息

复制`config.ini.example`并命名为`config.ini`，并根据实际情况修改`config.ini`的参数

## 常规使用

默认从腾讯漫画下载，注意鼠绘漫画和腾讯漫画的id区别

- 下载海贼王最新一集: `python3 -m onepiece`
- 下载漫画 id=505430 最新一集: `python3 -m onepiece --comicid=505430`
- 下载漫画 id=505430 所有章节: `python3 -m onepiece --comicid=505430 --all`
- 下载漫画 id=505430 第800集: `python3 -m onepiece --comicid=505430 --chapter=800`
- 下载漫画 id=505430 倒数第二集: `python3 -m onepiece --comicid=505430 --chapter=-2`
- 下载漫画 id=505430 1到5集,7集，9到10集: `python3 -m onepiece --comicid=505430 --chapter=1-5,7,9-10`
- 下载漫画 id=505430 并生成pdf文件: `python3 -m onepiece --comicid=505430 --pdf`
- 下载漫画 id=505430 并推送到邮箱: `python3 -m onepiece --comicid=505430 --pdf --mail`

从鼠绘漫画下载:

- 从鼠绘漫画下载海贼王最新一集: `python3 -m onepiece --site=ishuhui`
- 从鼠绘漫画下载 id=1 所有章节: `python3 -m onepiece --site=ishuhui --comicid=1 --all`
- 从鼠绘漫画下载 id=1 第800集: `python3 -m onepiece --site=ishuhui --comicid=1 --chapter=800`
- 从鼠绘漫画下载 id=1 倒数第二集: `python3 -m onepiece --site=ishuhui --comicid=1 --chapter=-2`
- 从鼠绘漫画下载 id=1 1到5集,7集，9到10集: `python3 -m onepiece --site=ishuhui --comicid=1 --chapter=1-5,7,9-10`
- 从鼠绘漫画下载 id=1 并生成pdf文件: `python3 -m onepiece --site=ishuhui --comicid=1 --pdf`
- 从鼠绘漫画下载 id=1 并推送到邮箱: `python3 -m onepiece --site=ishuhui --comicid=1 --pdf --mail`


## 使用帮助

```
usage: onepiece [-h] [-id COMICID] [--name NAME] [-c CHAPTER]
                   [--worker WORKER] [--all] [--pdf] [--mail]
                   [--config CONFIG] [-o OUTPUT] [--site {qq,ishuhui}] [-V]

optional arguments:
  -h, --help            show this help message and exit
  -id COMICID, --comicid COMICID
                        漫画id，海贼王: 505430
                        (http://ac.qq.com/Comic/ComicInfo/id/505430)
  --name NAME           漫画名
  -c CHAPTER, --chapter CHAPTER
                        要下载的章节, 默认下载最新章节。如 -c 666 或者 -c 1-5,7,9-10
  --worker WORKER       线程池数，默认开启4个线程池
  --all                 若设置了则下载该漫画的所有章节, 如 --all
  --pdf                 若设置了则生成pdf文件, 如 --pdf
  --mail                若设置了则发送到邮箱, 如 --mail。需要预先配置邮件信息。
                        可以参照config.ini.example文件，创建并修改config.ini文件
  --config CONFIG       配置文件路径，默认取当前目录下的config.ini
  -o OUTPUT, --output OUTPUT
                        文件保存路径，默认保存在当前路径下的download文件夹
  --site {qq,ishuhui}   数据源网站：支持qq,ishuhui
  -V, --version         show program's version number and exit

```

**免责声明**：本项目仅供学习交流之用，请勿用于非法用途。
