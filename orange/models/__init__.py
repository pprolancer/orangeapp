import os
import glob
import datetime
import decimal
from sqlalchemy.ext.declarative import declarative_base

from orange.common.exceptions import CommonBaseException

Base = declarative_base()


class ModelValueError(CommonBaseException):
    pass


def get_base_class_by_table_name(table_name):
    if not getattr(Base, '_tbl_cls_maps', None):
        Base._tbl_cls_maps = {}
        for cls in Base._decl_class_registry.values():
            if not hasattr(cls, '__tablename__'):
                continue
            Base._tbl_cls_maps[cls.__tablename__] = cls
    return Base._tbl_cls_maps[table_name]


def record_to_dict(record):
    data = {}
    for k, v in record.__dict__.items():
        if k.startswith('_'):
            continue
        if isinstance(v, datetime.datetime):
            data[k] = v.isoformat() + 'Z'
        elif isinstance(v, datetime.date):
            data[k] = v.isoformat()
        elif isinstance(v, decimal.Decimal):
            data[k] = float(v)
        else:
            data[k] = v

    return data


def to_dict(obj, fields=None, fields_map={}, extra_fields=None):
    '''
    convert a sqlalchemy object to a python dict.
    @param fields: list of fields which we want to show in return value.
        if fields=None, we show all fields of sqlalchemy object
    @type fields: list
    @param fields_map: a map converter to show fields as a favorite.
        every field can bind to a lambda function in fields_map.
        if a field was bind to a None value in fields_map, we ignore this field
        to show in result
    @type fields_map: dict
    '''
    data = {}

    if fields is None:
        fields = obj.__table__.columns.keys()
    fields.extend(extra_fields or [])
    for field in fields:
        if field in fields_map:
            if fields_map[field] is None:
                continue
            v = fields_map.get(field)()
        else:
            v = getattr(obj, field, None)
        if isinstance(v, datetime.datetime):
            data[field] = v.isoformat() + 'Z'
        elif isinstance(v, datetime.date):
            data[field] = v.isoformat()
        elif isinstance(v, decimal.Decimal):
            data[field] = float(v)
        else:
            data[field] = v

    return data


__all__ = []
files = glob.glob(os.path.dirname(__file__) + "/*.py")
for f in files:
    if os.path.isfile(f) and not os.path.basename(f).startswith('_'):
        mod = os.path.basename(f)[:-3]
        exec ("import %s" % mod)
        __all__.append(mod)
