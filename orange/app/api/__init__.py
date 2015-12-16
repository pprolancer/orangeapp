from functools import wraps
from flask_login import login_user
from flask import request, current_app, Response

from orange.models.user import User
from orange.db import global_session


def basic_unauthorized():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to be authorized with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def login_using_authorization_header(log):
    auth = request.authorization
    api_key = None
    if auth and auth.username == 'key':
        api_key = auth.password
    else:
        auth = request.headers.get("Authorization", None)
        if auth and auth.startswith('key='):
            api_key = auth[4:]

    if not api_key:
        log.error("invalid Authorization pattern: %s", auth)
        return

    dbs = global_session()
    user = dbs.query(User).filter_by(api_key=api_key).first()
    if user:
        login_user(user)


def login_api_key(fun):
    """
    fun: login_required function
    use basic authorization headers
    """
    @wraps(fun)
    def auto_login_api_key_wrapper(*args, **kwargs):
        login_using_authorization_header(current_app.logger)

        return fun(*args, **kwargs)
    return auto_login_api_key_wrapper
