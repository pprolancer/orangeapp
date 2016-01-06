#!/usr/bin/env python
"""Basic test package which will be inherited by other tests.
"""
import json
import unittest
import logging

from flask.app import Flask
from flask.ext.testing import TestCase

from orange.myproject.db import switch_engine, create_all, drop_all, \
    new_session
from orange.myproject.models import Base

logger = logging.getLogger()


class SqlAlchemyTest(unittest.TestCase):
    def __init__(self, *args, **kw):
        self.dbs = None
        unittest.TestCase.__init__(self, *args, **kw)

    def setUp(self):
        self.dbs = new_session()

    def tearDown(self):
        self.dbs and self.dbs.close()

    def add_to_db(self, objects, commit=True):
        if not isinstance(objects, (list, set, tuple)):
            objects = [objects]

        self.dbs.add_all(objects)
        if commit:
            self.dbs.commit()

    @classmethod
    def setUpClass(cls):
        switch_engine(test=True)
        cls.dbs = new_session()
        create_all(Base)

    @classmethod
    def tearDownClass(cls):
        drop_all(Base)


class FlaskAppTest(TestCase, SqlAlchemyTest):
    """Basic test class which inherits from TestCase. Other than providing an
    app, it sets a unique dbname to be used when creating an app & initializing
    db connection.
    """

    def register_blueprint(self, app):
        raise NotImplementedError()

    def create_app(self):
        app = Flask(self.__class__.__name__)

        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'VERYSECRET'
        app.url_map.strict_slashes = False

        self.register_blueprint(app)

        self.app = app
        return app

    @classmethod
    def setUpClass(cls):
        SqlAlchemyTest.setUpClass()

    def post(self, path, **data):
        headers = getattr(self, 'headers', None)
        return self.client.post(path, content_type='application/json',
                                data=json.dumps(data), headers=headers)

    def put(self, path, **data):
        headers = getattr(self, 'headers', None)
        return self.client.put(path, content_type='application/json',
                               data=json.dumps(data), headers=headers)

    def get(self, path):
        headers = getattr(self, 'headers', None)
        return self.client.get(path, content_type='application/json',
                               headers=headers)

    def delete(self, path, **data):
        headers = getattr(self, 'headers', None)
        return self.client.delete(path, content_type='application/json',
                                  data=json.dumps(data), headers=headers)
