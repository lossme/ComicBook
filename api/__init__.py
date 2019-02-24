from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False

    from .views import app as main_app
    app.register_blueprint(main_app)

    return app
