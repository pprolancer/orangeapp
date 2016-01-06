from formencode import Schema, validators, Invalid
from formencode.api import Validator
from formencode.validators import _
import dateutil.parser
from decimal import Decimal, InvalidOperation
from datetime import datetime


class IgnoreKeyMissed(object):
    '''
    dummy class to pass to a if_missing field in formeencode Schema.
    when we want to ignore appearing of a field when missed, we will
    set if_missing=IgnoreKeyMissed.
    '''


class DummyValidator(Validator):
    '''
    a dummy Validator for MDMSchema.
    all fields with this type of validator will ignore,
    so not important what is that value.
    '''
    if_missing = IgnoreKeyMissed

    def _to_python(self, value, state):
        return IgnoreKeyMissed


class BaseSchema(Schema):
    """
    new Implementation of formencode Schema to cover some deficits
    """

    def _to_python(self, value_dict, state):
        value_dict = super(BaseSchema, self)._to_python(value_dict, state)

        for k, v in value_dict.items():
            if v == IgnoreKeyMissed:
                value_dict.pop(k)
        return value_dict


class ISODateTimeValidator(validators.String):
    '''
    a validator to validate an str in iso format.
    e.g: 2014-01-16T10:22:51.585719 or 2014-01-16T10:22:51
    '''
    messages = dict(
        invalidIso=_('Invalid iso datetime format'))

    def _to_python(self, value, state):
        if not value:
            return None
        try:
            return dateutil.parser.parse(value.rstrip('Z'))
        except (ValueError, TypeError):
            raise Invalid(self.message('invalidIso', state), value, state)

    def empty_value(self, value):
        return None


class ISODateValidator(ISODateTimeValidator):
    '''
    a validator to validate an str in iso format.
    e.g: 2014-01-16T10:22:51.585719 or 2014-01-16T10:22:51
    '''
    messages = dict(
        invalidIso=_('Invalid iso date format'))

    def _to_python(self, value, state):
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            raise Invalid(self.message('invalidIso', state), value, state)


class DecimalValidator(validators.RangeValidator):
    '''
    Validate a numeric string and return a Decimal
    '''

    messages = {'bad_value': 'Please enter a number'}

    def _to_python(self, value, state):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            raise Invalid(self.message('bad_value', state), value, state)
