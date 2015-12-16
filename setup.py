from setuptools import setup, find_packages

__version__ = 'dev'

setup(
    name='orangeapp',  # replace name of your project here
    version=__version__,
    author='pprolancer@gmail.com',
    description='Orange App',
    packages=find_packages(),
    include_package_data=True,
    data_files=[
        ('/etc/orange/orangeapp',
         ['orange/conf/config.ini']),
    ],
    entry_points={
        'console_scripts': [
            'orangeapp_db = orange.scripts.database:main',
        ],
    },
    dependency_links=[
    ],
    install_requires=[
        'simplejson',
        'uwsgi',
        'flask',
        'flask-login',
        'flask-principal',
        'flask-testing',
        'formencode',
        'pycrypto',
        'bcrypt',
        'pytz',
        'requests',
        'python-dateutil',
        'sqlalchemy',
        'sqlalchemy-utils',
        'sqlalchemy-migrate',
        'flask-sqlalchemy',
        'itsdangerous',
        'httplib2',
        'ua-parser',
        'user-agents',
    ],
    classifiers=['Development Status :: 1 - Production/Beta',
                 'Environment :: Web Environment',
                 'Intended Audience :: Developers',
                 'Operating System :: OS Independent',
                 'Topic :: Internet :: WWW/HTTP',
                 'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
                 'Topic :: Software Development :: Libraries :: Application Frameworks',
                 'Topic :: Software Development :: Libraries :: Python Modules', ],
)
