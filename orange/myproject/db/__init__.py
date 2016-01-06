from flask import g
from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from orange.myproject.conf import config

engine = None
DBSession = None

DB_URL = config.get('db', 'SQLALCHEMY_DATABASE_URI')
DB_URL_TEST = 'sqlite:///:memory:'


def get_engine():
    if engine is None:
        switch_engine()
    return engine


def switch_engine(new_engine=None, test=False):
    global engine
    global DBSession
    extra_args = {}
    is_sqlite = DB_URL.startswith('sqlite')
    is_debug = config.getboolean('db', 'debug')
    if not is_sqlite:
        extra_args = {'pool_size': 100, 'max_overflow': 0}
    if new_engine is None:
        if test:
            new_engine = create_engine(DB_URL_TEST, echo=is_debug)
        else:
            new_engine = create_engine(DB_URL, echo=is_debug, **extra_args)

    engine = new_engine
    DBSession = sessionmaker(bind=engine)


def new_session():
    if DBSession is None:
        switch_engine()

    return DBSession()


def global_session(create=True):
    dbs = getattr(g, 'dbs', None)
    if dbs:
        return dbs
    if create:
        g.dbs = new_session()
        return g.dbs
    return None


def create_all(Base):
    if engine is None:
        switch_engine()
    Base.metadata.create_all(engine)


def drop_all(Base):
    if engine is None:
        switch_engine()

    Base.metadata.drop_all(engine)
