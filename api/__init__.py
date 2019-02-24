from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False

    from .views import app as main_app
    app.register_blueprint(main_app)

    app.add_url_rule("/", "index", index)

    return app


def index():
    return jsonify(
        {
            "api_status": "ok",
            "example": [
                "/comic/ishuhui/1",
                "/comic/ishuhui/1/933",
                "/comic/qq/505430",
                "/comic/qq/505430/933",
                "/comic/wangyi/5015165829890111936",
                "/comic/wangyi/5015165829890111936/933",
                "/search/qq?name=海贼王",
                "/search/wangyi?name=海贼王"
            ]
        }
    )
