from flask import Blueprint
from flask_login import login_user, logout_user, current_user
from flexrest import RestApiResource, RestApiHandler

from .schema import LoginSchema
from orange.myproject.models.user import User
from orange.myproject.models import to_dict
from orange.myproject.app.api import login_api_key
from orange.myproject.common.helper import login_required

session = Blueprint('session_rest', __name__)


def user_info(user, fields=None):
    '''
    return needed user info for return in get and get_all handler.
    '''
    if not user:
        return None

    if fields is None:
        fields = User.__table__.columns.keys() + ['role', '_role']
    return to_dict(user, fields=fields, fields_map=dict(
        password=None,
        api_key=None,
        role=lambda: user.get_role(),
        _role=lambda: {
            'name': user._role.name,
            'title': user._role.title
        }
    ))


class SessionRestApiHandler(RestApiHandler):

    def login(self):
        data = self.validate_data(LoginSchema)
        username = data['username']
        password = data['password']
        remember = (data.get('remember', False) is True)

        dbs = self.get_db_session()

        user = self.get_query(dbs, User).filter(User.username == username
                                                ).first()
        if not user or not user.check_password(password):
            return self.jsonify_status(403, 'Login failed',
                                       reason='Wrong username or password')
        login_user(user, remember=remember)
        return self.jsonify_status(message="login successful",
                                   user=user_info(user))

    def logout(self):
        try:
            logout_user()

            return self.jsonify_status(message='User logged out')

        except Exception, e:
            self.logger.exception(e)
            self.abort_jsonfiy(400, 'error in logged out', reason=str(e))

    def get(self):
        params = {'user': user_info(current_user)}
        return self.jsonify_status(message='Current user session loaded',
                                   **params)


session_resource = RestApiResource(
    name="session",
    route="/session",
    app=session,
    handler=SessionRestApiHandler(),
    actions=['login', 'logout', 'get'],
    extra_handlers={'login': 'POST', 'logout': 'DELETE', 'get': 'GET'},
    decorators={
        'logout': [login_required(), login_api_key],
        'get': [login_required(), login_api_key]
    },
    needs_id=[])
