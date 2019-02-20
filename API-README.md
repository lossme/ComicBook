## 接口部署

安装依赖
```sh
pip install requests flask cachetools gunicorn
```

启动接口
```sh
gunicorn 'api:create_app()' -b "127.0.0.1:8000" --workers=2 --timeout=30
```

## 接口文档

`GET /api/<site>/<id>`

请求示例
```sh
curl ${host}/api/ishuhui/1
```

```json
{
  "desc": "<p>《ONE PIECE》（海賊王、航海王）簡稱“OP”，是日本漫畫家尾田榮一郎作畫的少年漫畫作品。在《週刊少年Jump》1997年34號開始連載。</p><p>描寫了擁有橡皮身體戴草帽的青年路飛，以成為“海賊王”為目標和同伴在大海展開冒險的故事。另外有同名的海賊王劇場版、電視動畫和遊戲等周邊媒體產品。</p><p>擁有財富、名聲、權力，這世界上的一切的男人 “海賊王”哥爾·D·羅傑，在被行刑受死之前說了一句話，讓全世界的人都湧向了大海。“想要我的寶藏嗎？如果想要的話，那就到海上去找吧，我全部都放在那裡。”，世界開始迎接“大海賊時代”的來臨。</p><p>時值“大海賊時代”，為了尋找傳說中海賊王羅傑所留下的大秘寶“ONE PIECE”，無數海賊揚起旗幟，互相爭鬥。一個叫路飛的少年為了與因救他而斷臂的香克斯的約定而出海，在旅途中不斷尋找志同道合的夥伴，開始了以成為海賊王為目標的偉大冒險旅程。</p>",
  "max_chapter_number": 933,
  "name": "海賊王",
  "source_name": "鼠绘漫画"
}
```

------


`GET /api/<site>/<id>/<chapter>`

请求示例
```sh
curl ${host}/api/ishuhui/1/933
```

```json
{
  "chapter_number": 933,
  "chapter_title": "武士的仁慈",
  "desc": "<p>《ONE PIECE》（海賊王、航海王）簡稱“OP”，是日本漫畫家尾田榮一郎作畫的少年漫畫作品。在《週刊少年Jump》1997年34號開始連載。</p><p>描寫了擁有橡皮身體戴草帽的青年路飛，以成為“海賊王”為目標和同伴在大海展開冒險的故事。另外有同名的海賊王劇場版、電視動畫和遊戲等周邊媒體產品。</p><p>擁有財富、名聲、權力，這世界上的一切的男人 “海賊王”哥爾·D·羅傑，在被行刑受死之前說了一句話，讓全世界的人都湧向了大海。“想要我的寶藏嗎？如果想要的話，那就到海上去找吧，我全部都放在那裡。”，世界開始迎接“大海賊時代”的來臨。</p><p>時值“大海賊時代”，為了尋找傳說中海賊王羅傑所留下的大秘寶“ONE PIECE”，無數海賊揚起旗幟，互相爭鬥。一個叫路飛的少年為了與因救他而斷臂的香克斯的約定而出海，在旅途中不斷尋找志同道合的夥伴，開始了以成為海賊王為目標的偉大冒險旅程。</p>",
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
  "max_chapter_number": 933,
  "name": "海賊王",
  "source_name": "鼠绘漫画"
}
```
