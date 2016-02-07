from setuptools import setup, find_packages

__version__ = 'dev'

setup(
    name='myproject',  # replace name of your project here
    version=__version__,
    author='pprolancer@gmail.com',
    description='Orange App',
    packages=find_packages(),
    include_package_data=True,
    data_files=[
        ('/etc/orange/myproject',
         ['orange/myproject/conf/config.ini']),
    ],
    entry_points={
        'console_scripts': [
            'myproject_db = orange.myproject.scripts.database:main',
        ],
    },
    dependency_links=[
    ],
    install_requires=[
        'flexrest',
        'flask-sqlalchemy',
        'flask-testing',
        'flask-login',
        'flask-principal',
        'flask',
        'sqlalchemy-migrate',
        'sqlalchemy-utils',
        'sqlalchemy',
        'pycrypto',
        'formencode',
        'bcrypt',
        'pytz',
        'itsdangerous',
        'requests',
        'python-dateutil',
        'httplib2',
        'ua-parser',
        'user-agents',
        'uwsgi',
        'simplejson',
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
