from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False
    app.url_map.strict_slashes = False

    from .views import app as main_app
    app.register_blueprint(main_app)
    app.add_url_rule('/', 'index', index)

    return app


def index():
    return jsonify(
        {
            "api_status": "ok",
            "example": [
                "/api/qq?name=海贼王",
                "/api/qq/505430",
                "/api/qq/505430/933",

                "/api/u17?name=雏蜂",
                "/api/u17/195",
                "/api/u17/195/274",

                "/api/bilibili?name=海贼王",
                "/api/bilibili/24742",
                "/api/bilibili/24742/1"
            ]
        }
    )
