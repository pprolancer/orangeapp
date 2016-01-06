# -*- coding: utf-8 -*-
import sys
import random
import string
import hashlib
import logging
from glob import iglob
from threading import Thread
from functools import wraps, update_wrapper
from datetime import datetime, date
from logging import FileHandler, Formatter
from os.path import basename, relpath, sep, splitext
from flask import jsonify, url_for, json, g, abort as flask_abort
from flask import make_response
from flask.globals import current_app, request
from flask.ext.login import current_user
from werkzeug.exceptions import HTTPException


def pf(s, new_line=True):
    '''
    print with flush
    '''
    sys.stdout.write(s + '\n' if new_line else '')
    sys.stdout.flush()


def mkdirs(file_path):
    import os.path

    path = os.path.dirname(file_path)
    if not os.path.exists(os.path.abspath(path)):
        os.makedirs(os.path.abspath(path))


def jsonify_status_string(status_code=200, message=None, *args, **kw):
    response = jsonify(*args, **kw)
    response.status_code = response.code = status_code
    if message is not None:
        response.status = '%d %s' % (status_code, str(message))

    return response


def abort(response, status_code=None):
    if isinstance(response, basestring):
        response = make_response(response)
    if status_code:
        response.status_code = status_code
    e = HTTPException(response=response)
    e.code = getattr(response, 'status_code', 0)
    raise e


def abort_jsonify(code, message, *args, **kwargs):
    response = jsonify_status_string(code, message, *args, **kwargs)
    abort(response)


def setup_logger(log_format=None, log_file=None, level=logging.DEBUG):
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    if not log_format:
        log_format = '%(asctime)s - %(levelname)s - %(message)s'

    if not log_file:
        logging.basicConfig(format=log_format, level=level)
    else:
        mkdirs(log_file)
        logging.basicConfig(format=log_format, level=level, filename=log_file)


def init_flask_logger(app, log_format, log_root_level, log_file_path,
                      log_file_log_level):
    if log_format:
        app.debug_log_format = log_format

    # setup root log format - global filter.
    app.logger.setLevel(log_root_level)

    # make sure the folder exists. the python thread should has
    # permission to visit folder.
    mkdirs(log_file_path)
    file_handler = FileHandler(log_file_path)
    file_handler.setLevel(log_file_log_level)
    file_handler.setFormatter(Formatter(log_format))
    app.logger.addHandler(file_handler)
    app.logger.info('Flask Logger has been setup.')


def random_id(n=8, no_upper=False, no_lower=False, no_digit=False):
    rand = random.SystemRandom()
    chars = ''
    if no_upper is False:
        chars += string.uppercase
    if no_lower is False:
        chars += string.lowercase
    if no_digit is False:
        chars += string.digits
    if not chars:
        raise Exception('chars is empty! change function args!')

    return ''.join([rand.choice(chars) for _ in range(n)])


def import_submodules(__path__to_here):
    """
    Imports all submodules.
    Import this function in __init__.py and put this line to it:
    __all__ = import_submodules(__path__)
    """
    result = []
    for smfile in iglob(relpath(__path__to_here[0]) + "/*.py"):
        submodule = splitext(basename(smfile))[0]
        importstr = ".".join(smfile.split(sep)[:-1])
        if not submodule.startswith("_"):
            try:
                __import__(importstr + "." + submodule)
                result.append(submodule)
            except:
                pass
    return result


def get_remote_addr():
    if 'X-Forwarded-For' not in request.headers:
        remote_addr = request.remote_addr or 'untrackable'
    else:
        remote_addr = request.headers.getlist("X-Forwarded-For")[0]

    return remote_addr


def current_datetime(utc=True):
    return datetime.utcnow() if utc else datetime.now()


def md5(data):
    return hashlib.md5(data).hexdigest()


def get_url_for(endpoint, **kwargs):
    if g.subdomain:
        kwargs['subdomain'] = g.subdomain
    url = url_for(endpoint, **kwargs)
    return url


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, ' \
                                            'must-revalidate, post-check=0, ' \
                                            'pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


def json_loads_safe(s, none_if_failed=False, **kwargs):
    try:
        return json.loads(s, **kwargs)
    except:
        return None if none_if_failed else s


def to_bool(value):
    return str(value).lower() in ("yes", "y", "true", "t", "1")


def date_to_iso(dt, tz=False):
    if not dt:
        return None
    return dt.isoformat() + ('Z' if tz else '')


def starize_string(s, start=3, end=3, star_char='*'):
    return s[:start] + (len(s) - start - end) * star_char + s[-end:]


def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()

    return wrapper


def login_required(roles=None):
    if roles and not isinstance(roles, (list, tuple)):
        roles = [roles]

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or \
                    not current_user.is_authenticated():
                return current_app.login_manager.unauthorized()

            urole = current_user.get_role()
            if (roles and (urole not in roles)):
                flask_abort(403)
            return fn(*args, **kwargs)

        return decorated_view

    return wrapper


def has_permissions(permissions, abort=False):
    if not current_user.is_authenticated():
        return current_app.login_manager.unauthorized()

    if current_user.is_admin_role():
        return True

    if not isinstance(permissions, (list, tuple)):
        permissions = [permissions]

    role_permissions = current_user._role.permissions
    for permission in permissions:
        if permission not in role_permissions:
            if not abort:
                return False
            flask_abort(403)
    return True


def permission_required(permissions, method=None):
    from orange.myproject.models.user import RolePermission
    if not isinstance(permissions, (list, tuple)):
        permissions = [permissions]
    RolePermission.ALL_PERMISSIONS.update(permissions)

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not method or request.method == method:
                has_permissions(permissions, abort=True)
            return fn(*args, **kwargs)

        return decorated_view

    return wrapper


def json_datetime_encoder(o):
    if type(o) is date or type(o) is datetime:
        return o.isoformat()+'Z'


def sum_safe(l):
    return reduce(lambda x, y: (x or 0) + (y or 0), l, 0)
