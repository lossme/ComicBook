from flask import current_app
from flask_login import (
    UserMixin,
    AnonymousUserMixin
)

from .. import login_manager


class User(UserMixin):

    def __init__(self, username, password, id, active=True):
        self.id = id
        self.username = username
        self.password = password
        self.active = active

    def get_id(self):
        return self.id

    def is_active(self):
        return self.active

    def verify(self, password):
        if not self.password:
            return True
        else:
            return self.password == password

    @classmethod
    def get_user_by_username(cls, username):
        users = current_app.config.get('USERS', [])
        for user_id, user in enumerate(users):
            if username == user['username']:
                return cls(username=user['username'], password=user['password'], id=user_id)


class MyAnonymousUser(AnonymousUserMixin):

    def __init__(self):
        self.username = 'anonymoususe'
        self.id = None
        self.password = ''
        self.active = True


@login_manager.user_loader
def load_user(user_id):
    if not current_app.config.get('USERS'):
        return MyAnonymousUser()

    user_id = int(user_id)
    user = current_app.config.get('USERS')[user_id]
    return User(username=user['username'], password=user['password'], id=user_id)
