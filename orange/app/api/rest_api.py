from flask import request, current_app
from werkzeug.wrappers import Response as ResponseBase
from formencode.api import Invalid
from orange.db import global_session
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from sqlalchemy import desc, asc

from orange.conf import config
from orange.models import to_dict, get_base_class_by_table_name
from orange.common.helper import jsonify_status_string, \
    login_required
from orange.app.api import login_api_key

from orange.models import Base
from orange.common.exceptions import CommonBaseException


class InvalidOrderField(CommonBaseException):
    pass


def validate_ordering(value, valid_fields):
    order_type = asc
    if value.startswith('-'):
        order_type = desc
        value = value[1:]

    orders = []
    for v in value.split(','):
        if v not in valid_fields:
            raise InvalidOrderField(
                'Invalid order [%s]! valid fields are: %s' % (v, valid_fields))
        v = '.'.join(v.split('.')[:2])
        orders.append(order_type(v))
    return orders


def get_joined_tables_by_order(order):
    tables = []
    if '.' not in order:
        return tables

    for o in order.split(','):
        if '.' not in o:
            continue

        splitted = o.lstrip('-').split('.')
        table_name = splitted[0]
        table = Base.metadata.tables.get(table_name)
        if table is None:
            raise InvalidOrderField('table %s does not exists' % table_name)

        if len(splitted) > 2:
            table = (table, splitted[2])
        if table not in tables:
            tables.append(table)

    return tables


class RestApiHandler(object):
    resource_class = None
    resource_name = None
    resource_field = None
    resources_field = None
    add_schema = None
    update_schema = None
    list_pagination = True
    list_default_order = 'id'
    need_to_join_with_related_tables_for_order = True
    need_validate_foreign_keys = True

    @property
    def logger(self):
        return current_app.logger

    def __init__(self):
        if self.resource_name is None:
            self.resource_name = self.resource_class and \
                self.resource_class.__name__
        if self.resource_field is None:
            self.resource_field = self.resource_name and \
                self.resource_name.lower()
        if self.resources_field is None:
            self.resources_field = self.resource_field and \
                self.resource_field + 's'

    def serialize(self, obj, fields=None):
        return to_dict(obj, fields)

    def get_query(self, dbs, resource_class=None):
        return dbs.query(resource_class or self.resource_class)

    def make_add_result(self, new_entity, dbs=None):
        return {
            self.resource_field: self.serialize(new_entity),
            'id': new_entity.id
        }

    def make_update_result(self, entity, dbs=None):
        return {self.resource_field: self.serialize(entity)}

    def make_delete_result(self, entity, dbs=None):
        return {}

    def make_get_result(self, entity, dbs=None):
        return {
            self.resource_field: self.serialize(entity,
                                                self.get_entity_fields_get())
        }

    def get_entity_fields_list(self):
        return self.resource_class.__table__.columns.keys()

    def get_entity_fields_get(self):
        return self.resource_class.__table__.columns.keys()

    def get_valid_orders_fields(self):
        return self.resource_class.__table__.columns.keys()

    def make_list_result(self, query, args, order, offset=0, limit=0,
                         dbs=None):
        query = query.order_by(*order)
        if self.list_pagination:
            total = query.count()
            query = query.offset(offset)
            if limit != 0:
                query = query.limit(limit)

        e_fields = self.get_entity_fields_list()
        entities = [self.serialize(r, e_fields) for r in query]
        result = {self.resources_field: entities}
        if self.list_pagination:
            result['pagination'] = {'offset': offset, 'limit': len(entities),
                                    'total': total}

        return result

    def make_list_query(self, args, dbs):
        query = self.get_query(dbs)
        if 'id' in args:
            query = query.filter_by(id=args['id'])

        return query

    def before_delete(self, entity, dbs=None):
        pass

    def before_update(self, entity, data, dbs=None):
        pass

    def before_get(self, entity, dbs=None):
        pass

    def before_add(self, data, dbs=None):
        pass

    def after_add(self, entity, dbs=None):
        pass

    def after_update(self, entity, dbs=None):
        pass

    def after_delete(self, entity, dbs=None):
        pass

    def after_get(self, entity, dbs=None):
        pass

    def on_add(self, entity, dbs=None):
        pass

    def on_update(self, entity, dbs=None):
        pass

    def on_delete(self, entity, dbs=None):
        pass

    __fks = None

    def get_foreign_keys(self):
        if not self.resource_class:
            return {}
        if self.__fks is None:
            self.__fks = {
                fk.parent.name: get_base_class_by_table_name(
                    fk._column_tokens[1])
                for fk in self.resource_class.__table__.foreign_keys
            }

        return self.__fks

    def validate_foreign_key(self, fk_col_name, ref_class, fk_value, dbs,
                             abort=True):
        fk_obj = self.get_query(dbs, resource_class=ref_class
                                ).filter_by(id=fk_value).first()
        if not fk_obj:
            message = '%s with id %s does not exists' % (ref_class.__name__,
                                                         fk_value)
            if abort:
                self.on_not_exists(message=message)
            return False
        return True

    def validate_foreign_keys(self, data, dbs):
        if not (self.need_validate_foreign_keys and data and dbs):
            return

        foreign_keys = self.get_foreign_keys() or {}
        for k, v in foreign_keys.items():
            fk_value = data.get(k, None)
            if fk_value:
                self.validate_foreign_key(k, v, fk_value, dbs)

    def validate_data(self, schema=None, data=None, dbs=None):
        data = data or request.json
        if schema is None:
            return data
        try:
            data = schema.to_python(data)
        except Invalid, e:
            self.on_invalid_arguments(e, data)

        return data

    def abort(self, response):
        e = HTTPException(response=response)
        e.code = getattr(response, 'status_code', 0)
        raise e

    def abort_jsonify(self, code, message, **kwargs):
        response = self.jsonify_status(code, message, **kwargs)
        self.abort(response)

    def jsonify_status(self, code=200, message=None, *args, **kwargs):
        return jsonify_status_string(code, message, *args, **kwargs)

    def on_duplicate(self, error, data, message=None):
        if message is None:
            message = '%s with given name already exists' % self.resource_name
        self.abort_jsonify(409, message)

    def on_not_exists(self, resource_id=None, message=None):
        if message is None:
            message = '%s with id %s does not exists' % (self.resource_name,
                                                         resource_id)
        self.abort_jsonify(404, message)

    def on_invalid_arguments(self, error=None, data=None):
        if isinstance(error, basestring):
            errors = error
        else:
            errors = error and error.unpack_errors()
        self.abort_jsonify(400, 'Invalid arguments',
                           reason=errors)

    def on_unhandled_error(self, error):
        self.abort_jsonify(400, 'Unhandled Error', reason=str(error))

    def add(self):
        data = self.validate_data(self.add_schema)

        dbs = global_session()
        self.before_add(data, dbs)
        self.validate_foreign_keys(data, dbs)
        db_fields = self.resource_class.__table__.columns.keys()
        model_data = {k: v for k, v in data.items() if k in db_fields}

        try:
            entity = self.resource_class(**model_data)
            dbs.add(entity)
            dbs.flush()
        except IntegrityError as e:
            dbs.rollback()
            self.on_duplicate(e, data)

        try:
            self.after_add(entity, dbs)
        except Exception as e:
            dbs.rollback()
            raise e
        dbs.commit()

        try:
            self.on_add(entity, dbs)
        except:
            pass

        result = self.make_add_result(entity, dbs)
        if isinstance(result, ResponseBase):
            return result

        return self.jsonify_status(
            message="%s successfully created" % self.resource_name, **result)

    def update(self, resource_id):
        dbs = global_session()
        query = self.get_query(dbs)
        entity = query.filter_by(id=resource_id).first()
        if entity is None:
            self.on_not_exists(resource_id)

        data = self.validate_data(self.update_schema, dbs=dbs)

        self.before_update(entity, data=data, dbs=dbs)
        self.validate_foreign_keys(data, dbs)

        db_fields = self.resource_class.__table__.columns.keys()
        model_data = {k: v for k, v in data.items() if k in db_fields}

        for k, v in model_data.iteritems():
            setattr(entity, k, v)
        try:
            dbs.flush()
        except IntegrityError as e:
            dbs.rollback()
            self.on_duplicate(e, data)

        try:
            self.after_update(entity, dbs)
        except Exception as e:
            dbs.rollback()
            raise e
        dbs.commit()

        try:
            self.on_update(entity, dbs)
        except:
            pass

        result = self.make_update_result(entity, dbs)
        if isinstance(result, ResponseBase):
            return result

        return self.jsonify_status(
            message='%s updated' % self.resource_name, **result)

    def delete(self, resource_id):
        dbs = global_session()
        query = self.get_query(dbs)
        entity = query.filter_by(id=resource_id).first()
        if entity is None:
            self.on_not_exists(resource_id)

        self.before_delete(entity, dbs)

        dbs.delete(entity)
        dbs.flush()
        try:
            self.after_delete(entity, dbs)
        except Exception as e:
            dbs.rollback()
            raise e
        dbs.commit()

        try:
            self.on_delete(entity, dbs)
        except:
            pass

        result = self.make_delete_result(entity, dbs)
        if isinstance(result, ResponseBase):
            return result

        return self.jsonify_status(
            message='%s deleted' % self.resource_name, **result)

    def get(self, resource_id):
        dbs = global_session()
        query = self.get_query(dbs)
        entity = query.filter_by(id=resource_id).first()
        if entity is None:
            self.on_not_exists(resource_id)

        self.before_get(entity, dbs)

        result = self.make_get_result(entity, dbs)

        self.after_get(entity, dbs)

        if isinstance(result, ResponseBase):
            return result

        return self.jsonify_status(
            message='%s details loaded' % self.resource_name, **result)

    def get_pagination_params(self, order_fields, default_order):
        try:
            offset = int(request.args.get('offset', 0))
            default_limit = config.getint('panel', 'UI_DEFAULT_PAGING_LIMIT')
            limit = int(request.args.get('limit', default_limit))
            order_param = request.args.get('order', default_order).strip()
            order = validate_ordering(order_param, valid_fields=order_fields)
        except InvalidOrderField as e:
            self.abort_jsonify(400, 'Invalid order argument',
                               reason=e.message)
        except ValueError, e:
            self.abort_jsonify(400, 'Invalid offset/limit arguments',
                               reason=str(e))
        return offset, limit, order

    def list(self):
        order_fields = self.get_valid_orders_fields()
        order_param = request.args.get('order',
                                       self.list_default_order).strip()

        offset, limit, order = self.get_pagination_params(
            order_fields, self.list_default_order)
        dbs = global_session()
        query = self.make_list_query(request.args, dbs)

        if self.need_to_join_with_related_tables_for_order:
            try:
                joined_tables = get_joined_tables_by_order(order_param)
            except InvalidOrderField as e:
                self.abort_jsonify(400, 'Invalid order argument',
                                   reason=e.message)

            for table in joined_tables:
                if isinstance(table, tuple):
                    query = query.outerjoin(
                        table[0], getattr(self.resource_class,
                                          table[1]) == table[0].columns['id'])
                else:
                    query = query.outerjoin(table)

        result = self.make_list_result(query, request.args, order, offset,
                                       limit, dbs)
        if isinstance(result, ResponseBase):
            return result

        return self.jsonify_status(
            message='%ss details loaded' % self.resource_name, **result)


class RestApiResource(object):

    """Represents a REST resource, with the different HTTP verbs"""
    _NEED_ID = ["get", "update", "delete"]
    _VERBS = {
        "get": "GET",
        "update": "PUT",
        "delete": "DELETE",
        "list": "GET",
        "add": "POST"
    }
    _track_last_activity_fn = None
    _permission_required_fn = None
    ALL_PERMISSIONS = set()

    def __init__(self, name, route, app, handler, actions=None,
                 identifier='resource_id', enforce_permitted=None,
                 extra_permissions=None, login_required=True,
                 extra_handlers=None, needs_id=None, ip_restricted=True,
                 trackable=True, track_last_activity=True):
        """
        :name:
            name of the resource. This is being used when registering
            the route, for its name and for the name of the id parameter
            that will be passed to the views

        :route:
           Default route for this resource

        :app:
            Application to register the routes onto

        :actions:
            Authorized actions. Optional. None means all.
            this can be list of strings or list of dict.
            list of dict can be in this format:
            {
                name: action_name,
                prefix: prefix_path,
            }
            in dict format mean we want to add a prefix path

        :handler:
            The handler instance which will handle the requests

        :identifier:
            this will be set as a arguments of _NEED_ID handlers

        :enforce_permitted:
            enforce to allow access for this actions.
            this ignore database checking
            enforce_permitted=["get", "list"]
        :ip_restricted:
            if True this will check Role ip restrictions.
            this can be a dict with key "action": True/False as well
            to customize for every action
        :trackable:
            if True this will track POST/PUT/DELETE actions in db.
            this can be a dict with key "action": True/False as well
            to customize for every action
        """
        if needs_id is not None:
            self._NEED_ID = needs_id
        if extra_handlers:
            self._VERBS = self._VERBS.copy()
            self._VERBS.update(extra_handlers)
        if not actions:
            actions = self._VERBS.keys()

        self._route = route
        self._handler = handler
        self._name = name
        self._identifier = identifier
        self._login_required = login_required
        self._enforce_permitted = enforce_permitted or []
        self._extra_permissions = extra_permissions
        self._ip_restricted = ip_restricted
        self._trackable = trackable
        self._track_last_activity = track_last_activity
        if extra_permissions:
            RestApiResource.ALL_PERMISSIONS.update(extra_permissions)

        for action in actions:
            self.add_url_rule(app, action)

    def _get_route_for(self, action, prefix=None):
        """Return the complete URL for this action.

        Basically:

         - get, update and delete need an id
         - add and list does not
        """
        route = self._route
        if prefix:
            route += '/%s' % prefix

        if action in self._NEED_ID and self._identifier is not None:
            route += "/<%s>" % self._identifier

        return route

    def add_url_rule(self, app, action):
        """Registers a new url to the given application, regarding
        the action.
        """
        prefix = None
        if isinstance(action, dict):
            name = action['name']
            prefix = action.get('prefix', name)
            action = name

        http_method = self._VERBS.get(action, "GET")
        method = getattr(self._handler, action)
        # check_permission = None
        _login_required = self._login_required
        # _enforce_permitted = action in self._enforce_permitted
        _ip_restricted = self._ip_restricted
        _trackable = self._trackable
        if isinstance(_login_required, dict):
            _login_required = _login_required.get(action, True)
        if isinstance(_ip_restricted, dict):
            _ip_restricted = _ip_restricted.get(action, True)
        if isinstance(_trackable, dict) and action in _trackable:
            _trackable = _trackable['action']
        else:
            _trackable = http_method in ('POST', 'PUT', 'DELETE')

        # if _login_required and self._permission_required_fn \
        #         and not _enforce_permitted:
        #     permission = '%s__%s' % (self._name, action)
        #     RestApiResource.ALL_PERMISSIONS.add(permission)
        #     method = self._permission_required_fn(permission)(method)
        # elif _login_required:
        #     method = login_required()(method)
        if _login_required:
            method = login_required()(method)
            method = login_api_key(method)

        if self._track_last_activity and self._track_last_activity_fn:
            method = self._track_last_activity_fn(method)

        app.add_url_rule(
            self._get_route_for(action, prefix),
            "%s_%s" % (self._name, action),
            method,
            methods=[http_method])
