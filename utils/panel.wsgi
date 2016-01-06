from orange.myproject.conf import config
from orange.myproject.app import create_app

application = create_app(config)
