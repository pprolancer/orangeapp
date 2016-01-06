import os
import sys
import imp
import optparse
from migrate.versioning import api
from migrate.exceptions import DatabaseAlreadyControlledError
from orange.myproject.common.shortcuts import get_or_create
from orange.myproject.db import create_all, drop_all, new_session
from orange.myproject.models import Base
from orange.myproject.models.user import User, Role, RolePermission
from orange.myproject.conf import config


SQLALCHEMY_DATABASE_URI = config.get('db', 'SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_MIGRATE_REPO = config.getpath('db', 'SQLALCHEMY_MIGRATE_REPO')


def init_db():
    import orange.myproject.app  # load all permissions
    print "++++ Initializing database with predefined records ..."
    ADMIN_PASS = 'test1234'
    dbs = new_session()
    admin_role = get_or_create(dbs, Role, commit=False,
                               name=Role.RESERVED['ADMIN'], title='Admin')
    user_role = get_or_create(dbs, Role, commit=False,
                              name=Role.RESERVED['USER'], title='User')
    admin_user, admin_created = get_or_create(
        dbs, User, commit=False, created_flag=True,
        username=User.RESERVED['ADMIN'], _role=admin_role)
    if admin_created:
        admin_user.set_password(ADMIN_PASS)
    user_default_permissions = [
        p for p in RolePermission.ALL_PERMISSIONS if p.startswith('dashboard:')
    ]
    user_role.permissions = user_default_permissions

    dbs.commit()

    if admin_created:
        print '++++ Added new admin user: username: "%s", password: "%s". ' \
            'please change the passwd in first login!' % (admin_user.username,
                                                          ADMIN_PASS)
    print '++++ db initialized.'
    dbs.close()


def install(initialize=True):
    create_all(Base)
    try:
        if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
            api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
            api.version_control(SQLALCHEMY_DATABASE_URI,
                                SQLALCHEMY_MIGRATE_REPO)
        else:
            api.version_control(SQLALCHEMY_DATABASE_URI,
                                SQLALCHEMY_MIGRATE_REPO,
                                api.version(SQLALCHEMY_MIGRATE_REPO))
    except DatabaseAlreadyControlledError:
        pass

    print "+++ Created all tables -> OK"

    if initialize:
        init_db()


def uninstall():
    drop_all(Base)
    dbs = new_session()
    dbs.execute('DROP table migrate_version')
    dbs.commit()
    print "--- Dropped all tables -> OK"


def reinstall(initialize=True):
    uninstall()
    install(initialize)


def prompt_migrate_vers(ver=None, db_ver=None):
    if db_ver is None:
        db_ver = api.db_version(SQLALCHEMY_DATABASE_URI,
                                SQLALCHEMY_MIGRATE_REPO)
    if ver is None:
        ver = api.version(SQLALCHEMY_MIGRATE_REPO)
    print 'Current database version: %s' % db_ver
    print 'Final repository version: %s' % ver
    print 30 * '='


def downgrade(step=1):
    db_ver = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    ver = api.version(SQLALCHEMY_MIGRATE_REPO)
    prompt_migrate_vers(ver, db_ver)

    if db_ver == 0:
        print '[No downgrade]'
        return
    target_ver = 0 if step == 0 else max(0, db_ver - step)
    api.downgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, target_ver)
    new_db_ver = str(api.db_version(SQLALCHEMY_DATABASE_URI,
                     SQLALCHEMY_MIGRATE_REPO))
    print '--- Downgraded to version: %s -> OK' % new_db_ver


def migrate():
    db_ver = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    ver = api.version(SQLALCHEMY_MIGRATE_REPO)
    prompt_migrate_vers(ver, db_ver)

    migration = SQLALCHEMY_MIGRATE_REPO + '/versions/%03d_migration.py' % (
        ver + 1)
    tmp_module = imp.new_module('old_model')
    old_model = api.create_model(SQLALCHEMY_DATABASE_URI,
                                 SQLALCHEMY_MIGRATE_REPO)
    exec old_model in tmp_module.__dict__
    script = api.make_update_script_for_model(SQLALCHEMY_DATABASE_URI,
                                              SQLALCHEMY_MIGRATE_REPO,
                                              tmp_module.meta, Base.metadata)
    open(migration, "wt").write(script)
    print '+++ New migration saved in: "%s"' % migration


def upgrade():
    db_ver = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    ver = api.version(SQLALCHEMY_MIGRATE_REPO)
    prompt_migrate_vers(ver, db_ver)

    if db_ver == ver:
        print '[No upgrade]'
        return

    api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    new_db_ver = str(api.db_version(SQLALCHEMY_DATABASE_URI,
                     SQLALCHEMY_MIGRATE_REPO))
    print '+++ Upgraded to version: %s -> OK' % new_db_ver


def parseOptions():
    '''
    parse program parameters
    '''
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--dbinfo', dest='db_info', action="store_true",
                      metavar='DB_INFO',
                      help='show current migration versions')
    parser.add_option('--init-db', dest='init_db', action="store_true",
                      metavar='INITIALIZE_DB',
                      help='show current migration versions')
    parser.add_option('--install', dest='install', action="store_true",
                      metavar='INSTALL', help='install and create all tables')
    parser.add_option('--no-init', dest='no_init', action="store_true",
                      default=False, metavar='NO_INIT',
                      help='avoid to initialize db')
    parser.add_option('--uninstall', dest='uninstall',
                      action="store_true", metavar='UNINSTALL',
                      help='uninstall and remove all tables')
    parser.add_option('--reinstall', dest='reinstall',
                      action="store_true", metavar='REINSTALL',
                      help='reinstall all tables')
    parser.add_option('--migrate', dest='migrate', action="store_true",
                      metavar='MIGRATE', help='generate migration script')
    parser.add_option('--upgrade', dest='upgrade', action="store_true",
                      metavar='UPGRADE', help='upgrade database')
    parser.add_option('--downgrade', dest='downgrade', action="store_true",
                      metavar='DOWNGRADE', help='downgrade database')
    parser.add_option('--down-step', dest='down_step', action="store",
                      type="int", default=1, metavar='DOWN_STEP',
                      help='downgrade step')
    options, args = parser.parse_args()
    return options, args, parser


def main():
    opt, args, parser = parseOptions()
    if opt.uninstall is True:
        uninstall()
    elif opt.install is True:
        install(not opt.no_init)
    elif opt.reinstall is True:
        reinstall(not opt.no_init)
    elif opt.migrate:
        migrate()
    elif opt.upgrade:
        upgrade()
    elif opt.downgrade:
        downgrade(opt.down_step)
    elif opt.db_info:
        prompt_migrate_vers()
    elif opt.init_db:
        init_db()
    else:
        parser.print_help()
        sys.exit(1)

    sys.exit(0)

if __name__ == '__main__':
    main()
