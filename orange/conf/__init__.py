import os
from decimal import Decimal
from ConfigParser import SafeConfigParser, NoOptionError

PROJECT_BASE_PATH = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

DEFAULT_CONF_PATH = os.path.join(PROJECT_BASE_PATH,
                                 'orange/conf/config.ini')
CUSTOM_CONF_PATH = os.getenv('ORANGEAPP_CONFIG_PATH', '') or \
    '/etc/orange/orangeapp/config.ini'


class NoDefault:
    pass


class Config(SafeConfigParser):
    def getpath(self, section, option, default=NoDefault):
        v = self.get(section, option, default=default)
        if not os.path.isabs(v):
            v = os.path.join(PROJECT_BASE_PATH, v)
        return v

    def getboolean(self, section, option, default=NoDefault):
        v = self.get(section, option, default=default)
        if v.lower() not in self._boolean_states:
            raise ValueError('Not a boolean: %s' % v)
        return self._boolean_states[v.lower()]

    def getint(self, section, option, default=NoDefault):
        return self._get(section, int, option, default=default)

    def getfloat(self, section, option, default=NoDefault):
        return self._get(section, float, option, default=default)

    def getdecimal(self, section, option, default=NoDefault):
        return self._get(section, Decimal, option, default=default)

    def getlist(self, section, option, default=NoDefault):
        v = self.get(section, option, default=default) or ''
        return [i.strip() for i in v.split(',') if i.strip()]

    def _get(self, section, conv, option, default=NoDefault):
        return conv(self.get(section, option, default=default))

    def get(self, section, option, raw=False, vars=None, default=NoDefault):
        try:
            v = SafeConfigParser.get(self, section, option, raw, vars)
        except NoOptionError:
            if default != NoDefault:
                return default
            raise
        return v

    def options_dict(self, section):
        return {opt: self.get(section, opt) for opt in self.options(section)}


config = Config()
config.read([DEFAULT_CONF_PATH, CUSTOM_CONF_PATH])
