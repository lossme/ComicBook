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
                "/info/ishuhui/1",
                "/info/ishuhui/1/933",
                "/info/qq/505430",
                "/info/qq/505430/933",
                "/info/wangyi/5015165829890111936",
                "/info/wangyi/5015165829890111936/933",
                "/search/qq?name=海贼王",
                "/search/wangyi?name=海贼王"
            ]
        }
    )
