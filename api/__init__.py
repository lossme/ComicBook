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
                "/api/ishuhui/1",
                "/api/ishuhui/1/933",
                "/api/qq/505430",
                "/api/qq/505430/933",
                "/api/wangyi/5015165829890111936",
                "/api/wangyi/5015165829890111936/933",
            ]
        }
    )
