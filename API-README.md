## 接口部署

安装依赖
```sh
pip install requests flask cachetools gunicorn
```

启动接口
```sh
gunicorn 'api:create_app()' -b "127.0.0.1:8000" --workers=2 --timeout=30

# 查看可选的配置选项 gunicorn --help
# 文档 http://docs.gunicorn.org/en/latest/settings.html
```

## 接口文档

- [1.1 获取概要信息](#11)
- [1.2 获取章节详情](#12)
- [1.3 搜索接口](#13)

### 1.1 获取概要信息

`GET /comic/<site>/<comicid>`

请求示例
```sh
curl ${host}/comic/ishuhui/1
```

```json
{
  "author": "尾田荣一郎",
  "cover_image_url": "http://oss.ishuhui.com/oldImg/cartoon/book/thumb/1/YDdFCpDpUAveOWJvxJRusmHb.jpg",
  "crawl_time": "2019-02-26 05:28:45",
  "desc": "《ONE PIECE》（海賊王、航海王）簡稱“OP”，是日本漫畫家尾田榮一郎作畫的少年漫畫作品。在《週刊少年Jump》1997年34號開始連載。描寫了擁有橡皮身體戴草帽的青年路飛，以成為“海賊王”為目標和同伴在大海展開冒險的故事。另外有同名的海賊王劇場版、電視動畫和遊戲等周邊媒體產品。擁有財富、名聲、權力，這世界上的一切的男人 “海賊王”哥爾·D·羅傑，在被行刑受死之前說了一句話，讓全世界的人都湧向了大海。“想要我的寶藏嗎？如果想要的話，那就到海上去找吧，我全部都放在那裡。”，世界開始迎接“大海賊時代”的來臨。時值“大海賊時代”，為了尋找傳說中海賊王羅傑所留下的大秘寶“ONE PIECE”，無數海賊揚起旗幟，互相爭鬥。一個叫路飛的少年為了與因救他而斷臂的香克斯的約定而出海，在旅途中不斷尋找志同道合的夥伴，開始了以成為海賊王為目標的偉大冒險旅程。",
  "chapters": [
    {
      "chapter_number": 1,
      "title": "ROMANCE DAWN"
    },
    {
      "chapter_number": 2,
      "title": "戴草帽的路飞"
    },
    ...
  ],
  "name": "海賊王",
  "source_name": "鼠绘漫画",
  "source_url": "https://www.ishuhui.com/comics/anime/1",
  "tag": "熱血,冒險,搞笑"
}
```

------

### 1.2 获取章节详情

`GET /comic/<site>/<comicid>/<chapter_number>`

请求示例
```sh
curl ${host}/comic/ishuhui/1/933
```

```json
{
  "chapter_number": 933,
  "image_urls": [
    "https://oss.ishuhui.com/img/comics/2019/02/daeab48f-2d6f-4a1d-8041-957613713ca7.png",
    "https://oss.ishuhui.com/img/comics/2019/02/08e08806-5fb5-47a2-8849-508a681d8d2e.png",
    "https://oss.ishuhui.com/img/comics/2019/02/22e4851b-0dbf-445b-989c-174e317a650c.png",
    "https://oss.ishuhui.com/img/comics/2019/02/68fe6033-8ce3-424a-9b54-6e9b442d099d.png",
    "https://oss.ishuhui.com/img/comics/2019/02/4e552f98-de23-49b8-9f36-7a3d1d322590.png",
    "https://oss.ishuhui.com/img/comics/2019/02/c126a8c8-301d-4e04-a6b4-ac1c469d425a.png",
    "https://oss.ishuhui.com/img/comics/2019/02/f5dfd51c-6d8b-4867-89a0-83fe99490a92.png",
    "https://oss.ishuhui.com/img/comics/2019/02/ebd65831-2d99-4e07-841f-6ccfdc708fe5.png",
    "https://oss.ishuhui.com/img/comics/2019/02/b1076e7c-b5b9-4478-955e-336d090f4987.png",
    "https://oss.ishuhui.com/img/comics/2019/02/3e20a7a3-68ee-421d-9669-45dd47b8890e.png",
    "https://oss.ishuhui.com/img/comics/2019/02/3f8f8052-634a-429e-b1e9-77987f617600.png",
    "https://oss.ishuhui.com/img/comics/2019/02/0b66f28c-a3fa-49da-a27e-0137ed405600.png",
    "https://oss.ishuhui.com/img/comics/2019/02/765c2ee6-d833-4d0b-9dcf-fb37814b5cb8.png",
    "https://oss.ishuhui.com/img/comics/2019/02/fa9c9952-911d-4ff6-8c82-63e2b01722eb.png",
    "https://oss.ishuhui.com/img/comics/2019/02/7ec43744-4f8d-4ccd-aafd-2c8ea28f5d78.png",
    "https://oss.ishuhui.com/img/comics/2019/02/03ba8c69-bdab-457f-9cee-d06fc1a13347.png",
    "https://oss.ishuhui.com/img/comics/2019/02/d82c7ac5-60dd-4d48-b24f-80b717a30e02.png",
    "https://oss.ishuhui.com/img/comics/2019/02/37ff3131-8ccc-4634-960f-ed944785465a.png",
    "https://oss.ishuhui.com/img/comics/2019/02/7b92e407-60d2-4f86-bad6-7970c7e6f9ff.jpeg"
  ],
  "source_url": "https://www.ishuhui.com/comics/detail/11363",
  "title": "武士的仁慈"
}
```

获取章节图片，并刷新图片链接
```sh
curl "${host}/comic/bilibili/28201/1?force_refresh=true"
```

------

### 1.3 搜索接口

`GET /search/<site>?name={name}&limit={limit}`

请求示例

```sh
curl "${host}/search/qq?name=海贼王&limit=20"
```

```json
{
  "search_result": [
    {
      "comicid": "505430",
      "cover_image_url": "https://manhua.qpic.cn/vertical/0/17_16_48_0e28c8aabf48e91d395689b5f6a7689f.jpg/420",
      "name": "航海王",
      "site": "qq",
      "source_url": "https://ac.qq.com/Comic/ComicInfo/id/505430"
    },
    {
      "comicid": "531616",
      "cover_image_url": "https://manhua.qpic.cn/vertical/0/17_17_06_cb4ba7f7af603a3380bb1e5ed415804b.jpg/420",
      "name": "航海王（番外篇）",
      "site": "qq",
      "source_url": "https://ac.qq.com/Comic/ComicInfo/id/531616"
    },
    {
      "comicid": "512062",
      "cover_image_url": "https://manhua.qpic.cn/vertical/0/17_16_53_6b94329a848ab290f2a7fe8926c002cc.jpg/420",
      "name": "航海王（全彩版）",
      "site": "qq",
      "source_url": "https://ac.qq.com/Comic/ComicInfo/id/512062"
    },
    {
      "comicid": "550529",
      "cover_image_url": "https://manhua.qpic.cn/vertical/0/17_17_19_cdfbe709316c877ccfb23c57ab393d46.jpg/420",
      "name": "中国贵州贵阳中等孩子的日常？",
      "site": "qq",
      "source_url": "https://ac.qq.com/Comic/ComicInfo/id/550529"
    },
    {
      "comicid": "549637",
      "cover_image_url": "https://manhua.qpic.cn/vertical/0/24_22_37_a4aba72ff67134b2a8d6faf3202973c3_1545662258373.jpg/420",
      "name": "抑郁症",
      "site": "qq",
      "source_url": "https://ac.qq.com/Comic/ComicInfo/id/549637"
    },
    {
      "comicid": "630588",
      "cover_image_url": "https://manhua.qpic.cn/vertical/0/26_17_12_a5b28a23f4d5df3cea863deb0a9b274c_1516957975778.jpg/420",
      "name": "天堂岛",
      "site": "qq",
      "source_url": "https://ac.qq.com/Comic/ComicInfo/id/630588"
    },
    {
      "comicid": "628782",
      "cover_image_url": "https://manhua.qpic.cn/vertical/0/20_13_12_02857f7dbb8f571550c5a8e0e8e3104a_1513746733413.jpg/420",
      "name": "济康传",
      "site": "qq",
      "source_url": "https://ac.qq.com/Comic/ComicInfo/id/628782"
    }
  ]
}
```
