from formencode import validators
from orange.myproject import BaseSchema


class LoginSchema(BaseSchema):
    allow_extra_fields = True

    login = validators.UnicodeString(min=1, max=256, strip=True)
    password = validators.UnicodeString(min=1, max=256, strip=True)
    remember = validators.StringBool(if_missing=False)
