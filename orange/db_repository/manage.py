#!/usr/bin/env python
from migrate.versioning.shell import main

from orange.conf import config

if __name__ == '__main__':
    SQLALCHEMY_DATABASE_URI = config.get('db', 'SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_MIGRATE_REPO = config.getpath('db', 'SQLALCHEMY_MIGRATE_REPO')

    main(url=SQLALCHEMY_DATABASE_URI, repository=SQLALCHEMY_MIGRATE_REPO,
         debug=False)
