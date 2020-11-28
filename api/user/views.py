import logging
from flask import (
    jsonify,
    Blueprint,
    request,
    redirect,
    render_template
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from .model import (
    User,
    MyAnonymousUser
)
from .. import login_manager

login_manager.login_view = "user.login"
login_manager.anonymous_user = MyAnonymousUser


logger = logging.getLogger(__name__)

app = Blueprint("user", __name__,
                url_prefix='/user',
                template_folder='tempaltes',
                static_folder='static')


@app.route("/login", methods=['GET', 'POST'])
def login():
    data = {}
    if request.method == 'GET':
        return render_template("login.html", data=data)

    username = request.form.get('username')
    password = request.form.get('password')
    user = User.get_user_by_username(username)
    logger.info('username=%s password=%s', username, password)
    if not user or not user.verify(password=password):
        data = dict(login_result='登录失败')
        return render_template("login.html", data=data)
    login_user(user, remember=True)
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    else:
        return jsonify(dict(login='sucess'))


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    return jsonify(dict(logout='sucess'))


@app.route('/info')
@login_required
def home():
    return jsonify(dict(username=current_user.username, user_id=current_user.id))
