import os
from flask_script import (
    Manager,
    Server
)

from api import create_app
from api import db


app = create_app(os.getenv('FLASK_CONFIG') or 'api.config.Config')
manager = Manager(app)
manager.add_command("runserver", Server(host="127.0.0.1", port=8000))


@manager.command
def createdb():
    app.config['SQLALCHEMY_ECHO'] = True
    db.create_all()


if __name__ == '__main__':
    manager.run()
