from flask import Flask
from flask_restplus import Api

api = Api(version='1.0', title='ComicBook Crawler', authorizations={}, ui=True)


def create_app():
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False

    from .views import app as main_app
    app.register_blueprint(main_app)

    return app
