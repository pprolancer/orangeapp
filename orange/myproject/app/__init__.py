import os
import sys
import logging
from flask import Flask, Blueprint, redirect
from flask.ext.login import LoginManager
from flexrest import FlexRestManager

from orange.myproject.conf import config
from orange.myproject.db import global_session
from orange.myproject.models.user import User
from orange.myproject.models import Base
from orange.myproject.common.helper import init_flask_logger, \
    jsonify_status_string, login_required
from orange.myproject.app.api import login_api_key, basic_unauthorized
from orange.myproject.app.api.session.rest_api import session as session_rest


general = Blueprint('general', __name__)


@general.route('/test/', methods=['GET'])
def api_fortestonly():
    return jsonify_status_string(message="Success", status='success')


@general.route('/test/secret', methods=['GET'])
@login_api_key
@login_required()
def api_secret_fortestonly():
    return jsonify_status_string(message="Success", status='success')


@general.route('/', methods=['GET'])
def index():
    return redirect('index.html')


LOG_FILE_PATH = config.getpath('app', 'LOG_FILE_PATH')
STATIC_PATH = config.getpath('app', 'STATIC_PATH')
API_URL_PREFIX = config.get('app', 'API_URL_PREFIX')

BLUEPRINTS = [
    (general, ''),
    session_rest
]


def register_blueprints(app, blueprints):
    for blueprint in blueprints:
        prefix = API_URL_PREFIX
        if isinstance(blueprint, tuple):
            blueprint, prefix = blueprint
        app.register_blueprint(blueprint, url_prefix=prefix)


def init_app_config(app, config):
    class CFG(object):
        pass

    cfg = CFG()
    for name in config.options('app'):
        setattr(cfg, name.upper(), config.get('app', name))

    cfg.PORT = config.getint('app', 'PORT')
    cfg.HOST = config.get('app', 'HOST')
    cfg.SQLALCHEMY_DATABASE_URI = config.get('db', 'SQLALCHEMY_DATABASE_URI')
    cfg.MAX_CONTENT_LENGTH = config.getint('app', 'MAX_CONTENT_LENGTH')
    cfg.DEBUG = config.getboolean('app', 'DEBUG')
    server_name = os.getenv('POOLCONTROL_SERVER_URL', '')
    if server_name:
        cfg.SERVER_NAME = server_name
        config.set('app', 'SERVER_NAME', server_name)

    app.config.from_object(cfg)


def init_logger(app):
    log_format = config.get('app', 'LOG_FORMAT')
    log_root_level = config.get('app', 'LOG_ROOT_LEVEL')
    log_file_path = config.get('app', 'LOG_FILE_PATH')
    log_file_log_level = config.get('app', 'LOG_FILE_LOG_LEVEL')
    init_flask_logger(app, log_format, log_root_level, log_file_path,
                      log_file_log_level)

    if config.getboolean('app', 'DEBUG'):
        app.logger.addHandler(logging.StreamHandler(sys.stderr))


def load_user(uid):
    dbs = global_session()

    user = dbs.query(User).get(uid)
    if not user or not user.is_active():
        return None
    return user


def create_app(config):

    app = Flask(__name__, static_url_path='', static_folder=STATIC_PATH)
    init_app_config(app, config)
    init_logger(app)

    app.url_map.strict_slashes = False

    lm = LoginManager()
    lm.unauthorized_handler(basic_unauthorized)
    lm.init_app(app)
    lm.user_loader(load_user)
    lm.session_protection = "strong"
    # this patch needs because chrome will ignore cookies when using ip.
    app.session_interface.get_cookie_domain = lambda _app: None

    flex = FlexRestManager(db_base=Base, db_session_callback=global_session)
    flex.init_app(app)

    register_blueprints(app, BLUEPRINTS)

    @app.after_request
    def after_request(response):
        dbs = global_session(create=False)
        dbs and dbs.close()
        return response

    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('images/favicon.ico')

    return app
