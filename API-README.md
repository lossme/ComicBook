## 接口部署

安装依赖
```sh
pip install -r requirements-api.txt
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

`GET /api/<site>/<comicid>`

请求示例
```sh
curl "http://127.0.0.1:8000/api/bilibili/24742"
```

```json
{
    "author": "尾田荣一郎 集英社",
    "chapters": [
        {
            "chapter_number": 1,
            "source_url": "https://manga.bilibili.com/m/mc24742/218087",
            "title": "ROMANCE DAWN冒险的序幕"
        },
        {
            "chapter_number": 2,
            "source_url": "https://manga.bilibili.com/m/mc24742/218093",
            "title": "戴草帽的路飞"
        }
    ],
    "cover_image_url": "http://i0.hdslb.com/bfs/manga-static/8cfad691e8717f8c189f2b5e93a39d272708f91a.jpg",
    "crawl_time": "2020-08-16 15:06:29",
    "desc": "【此漫画的翻译由版权方提供】拥有财富、名声、权力、这世界上的一切的男人 “海盗王”高路德·罗杰，在临死之前说了一句话，让全世界的人都涌向了大海。“想要我的财宝吗？想要的话，就去拿吧，我把世界上的一切都放在了那里！”，这个世界迎来了“大海盗时代”。",
    "name": "航海王",
    "source_name": "哔哩哔哩漫画",
    "source_url": "https://manga.bilibili.com/m/detail/mc24742",
    "tag": "奇幻,热血,冒险"
}
```

刷新漫画数据（漫画数据默认缓存10分钟）
```sh
curl "http://127.0.0.1:8000/api/bilibili/24742?force_refresh=true"
```

------

### 1.2 获取章节详情

`GET /api/<site>/<comicid>/<chapter_number>`

请求示例
```sh
curl "http://127.0.0.1:8000/api/bilibili/24742/1"
```

```json
{
    "chapter_number": 1,
    "image_urls": [
        "https://i0.hdslb.com/bfs/manga/a978a1834b3ad58fad020e56aaac9faaa0aa941a.jpg?token=73441250b03e3f16%3ANyuRMmMH4QSq3VoxAtaxG5yw%2Bd0%3D%3A1597561590",
        "https://i0.hdslb.com/bfs/manga/535548cebdd5d96cfa87247f07171ccebfa1efa7.jpg?token=73441250b03e3f16%3Awk76wOeUd7daRpAfc%2FHSs1Qkql0%3D%3A1597561590",
        "https://i0.hdslb.com/bfs/manga/f6e50a5bdd38af33c152f7929ee63325b519bfdc.jpg?token=73441250b03e3f16%3Ad57MJZIADxnHC%2FG9TkOIvlK1pLU%3D%3A1597561590"
    ],
    "source_url": "https://manga.bilibili.com/m/mc24742/218087",
    "title": "ROMANCE DAWN冒险的序幕"
}
```

获取章节图片，并刷新图片链接
```sh
curl "http://127.0.0.1:8000/api/bilibili/24742/1?force_refresh=true"
```

------

### 1.3 搜索接口

`GET /api/<site>?name={name}&page={page}`

请求示例

```sh
curl "http://127.0.0.1:8000/api/qq?name=海贼&page=1"
```

```json
{
    "search_result":[
        {
            "comicid":"505430",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/17_16_48_0e28c8aabf48e91d395689b5f6a7689f.jpg/420",
            "name":"航海王",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/505430"
        },
        {
            "comicid":"531616",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/17_17_06_cb4ba7f7af603a3380bb1e5ed415804b.jpg/420",
            "name":"航海王（番外篇）",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/531616"
        }
    ]
}
```
