import bcrypt
from hashlib import md5
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import Column, Integer, DateTime, String, Boolean, Unicode, \
    ForeignKey, UniqueConstraint, event

from orange.models import Base, ModelValueError
from orange.common.helper import current_datetime, random_id


def api_key_gen():
    return random_id(64)


class User(Base):
    __tablename__ = 'users'

    RESERVED = dict(
        ADMIN='admin',
    )

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True)
    password = Column(String(88))
    api_key = Column(String(64), default=api_key_gen)
    firstname = Column(Unicode(256))
    lastname = Column(Unicode(256))
    email = Column(String(120), unique=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    _role = relationship("Role", lazy='joined')
    role = association_proxy('_role', 'name')

    active = Column(Boolean, default=True)
    created = Column(DateTime, default=current_datetime)
    last_activity = Column(DateTime)
    last_login_at = Column(DateTime)
    current_login_at = Column(DateTime)
    last_login_ip = Column(String(32))
    current_login_ip = Column(String(32))
    login_count = Column(Integer, default=0)

    def __init__(self, *args, **kwargs):
        if 'password' in kwargs:
            self.set_password(kwargs.pop('password', ''))
        super(User, self).__init__(*args, **kwargs)

    @staticmethod
    def validate_username(target, value, oldvalue, initiator):
        if value in ('order', 'and', 'or'):
            raise ModelValueError('Invalid username: [%s]' % value)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%s' % (
            md5(self.email).hexdigest(), str(size))

    def is_active(self):
        return self.active

    def is_admin_role(self):
        return self._role.is_admin()

    def is_reserved(self):
        return self.username in self.RESERVED.values()

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('u8'), bcrypt.gensalt())

    def set_password(self, password):
        self.password = User.hash_password(password)

    def check_password(self, password):
        try:
            return bcrypt.hashpw(
                password.encode('u8'),
                self.password.encode('u8')) == self.password
        except ValueError:
            return False

    def get_role(self):
        return self.role

    def __repr__(self):
        return '<User %r>' % (self.username)


event.listen(User.username, 'set', User.validate_username)


class Role(Base):
    __tablename__ = 'roles'

    RESERVED = dict(
        ADMIN='admin',
        USER='user',
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True)
    title = Column(String(256))
    comment = Column(String(512))
    permissions = association_proxy(
        "role_permission_associations", "permission",
        creator=lambda p: RolePermission(permission=p))

    def __init__(self, **kwargs):
        if 'title' not in kwargs and 'name' in kwargs:
            name = kwargs['name'] or ''
            title = name.capitalize()
            kwargs.update({'name': name, 'title': title})
        return super(Role, self).__init__(**kwargs)

    def is_admin(self):
        return self.name == self.RESERVED['ADMIN']

    def is_reserved(self):
        return self.name in self.RESERVED.values()

    def add_permissions(self, dbs, *permissions):
        for permission in permissions:
            if permission not in self.permissions:
                self.permissions.append(permission)

    def __repr__(self):
        return '<Role(name=%s)>' % self.name
    __str__ = __repr__


class RolePermission(Base):
    __tablename__ = 'role_permissions'
    __table_args__ = (
        UniqueConstraint('role_id', 'permission',
                         name='role_id__permission__unique'),
    )
    ALL_PERMISSIONS = set()

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column('role_id', Integer, ForeignKey('roles.id',
                                                    ondelete="CASCADE"))
    role = relationship("Role", backref="role_permission_associations")
    permission = Column(String(256))

    def __repr__(self):
        return '<RolePermission(name=%s, role=%s)>' % (self.permission,
                                                       self.role)
    __str__ = __repr__
