#!/usr/bin/env python
import unittest

from orange.myproject.tests import SqlAlchemyTest
from orange.myproject.db import new_session
from orange.myproject.models.user import User


class SampleSqlAlchemyTest(SqlAlchemyTest):
    def test_users_count(self):
        COUNT = 10
        users = [User(username='user%s' % i) for i in range(COUNT)]
        self.add_to_db(users)

        self.assertEqual(self.dbs.query(User).count(), COUNT)


def load_user(_id):
    dbs = new_session()
    user = dbs.query.filter(User.id == _id).first()
    dbs.close()
    return user


if __name__ == '__main__':
    unittest.main()
