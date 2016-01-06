#!/usr/bin/env python

import optparse
from orange.myproject.app import create_app
from orange.myproject.conf import config
from werkzeug.contrib.profiler import ProfilerMiddleware


def parseOptions():
    '''
    parse program parameters
    '''
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--profile', dest='profile', action="store_true",
                      metavar='PROFILE', help='Profiling state')
    parser.add_option('--host', dest='host', metavar='HOST',
                      help='host server address')
    parser.add_option('--port', dest='port', metavar='PORT',
                      help='listen server port')
    parser.add_option('--debug', dest='debug', action="store_true",
                      metavar='DEBUG', help='Debugging state')
    parser.add_option('--dbdebug', dest='db_debug', action="store_true",
                      metavar='DB_DEBUG', help='DB Debugging state')
    parser.add_option('--no-server-name', dest='no_server_name',
                      action="store_true", metavar='NO_SERVER_NAME',
                      help='not using SERVER_NAME in flask config')
    options, args = parser.parse_args()
    return options, args, parser


def main():
    opt, args, parser = parseOptions()
    profile = debug = False
    if opt.profile is True:
        profile = True
    if opt.debug is True:
        debug = True
    if opt.db_debug is True:
        config.set('db', 'debug', 'True')
    if opt.host:
        config.set('app', 'HOST', opt.host)
    if opt.port:
        config.set('app', 'PORT', opt.port)
    if opt.no_server_name:
        config.remove_option('app', 'SERVER_NAME')

    app = create_app(config)
    if profile:
        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
        app.logger.info('Running app in Profile state...')

    app.run(host=app.config['HOST'], port=app.config['PORT'],
            debug=debug or app.debug)


if __name__ == '__main__':
    main()
