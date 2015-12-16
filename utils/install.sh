#! /bin/bash

BRANCH=master

if [ -n "$1" ]; then
    BRANCH=$1
fi

# install required softwares
# apt-get install postgresql postgresql-contrib postgresql-server-dev-all -y
apt-get install nginx -y
apt-get install python-dev -y
apt-get install libevent-dev python-all-dev -y
apt-get install libffi-dev -y
apt-get install python-pip -y
apt-get install git -y
pip install virtualenv

# create postgres user/grant

# setup codes
pip uninstall orangeapp -y

mkdir -p /opt/orange/
mkdir -p /usr/local/orange/orangeapp/log/
chmod 777 -R /usr/local/orange/orangeapp/log/

rm -rf /opt/orange/orangeapp
git clone https://pprolancer@bitbucket.org/pprolancer/orangeapp.git -b $BRANCH /opt/orange/orangeapp

cp -a /opt/orange/orangeapp/utils/deploy.sh /usr/local/bin/orangeapp_deploy
cp /opt/orange/orangeapp/utils/orangeapp_nginx.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/orangeapp_nginx.conf /etc/nginx/sites-enabled/orangeapp_nginx.conf
cp /opt/orange/orangeapp/utils/uwsgi/orangeapp_panel.conf /etc/init/

virtualenv /opt/orange/env
cd /opt/orange/orangeapp
../env/bin/python setup.py install

echo "+++ Installing database..."
../env/bin/orangeapp_db --install

# restart services
echo "Restarting Server..."
service nginx restart
service orangeapp_panel restart
service orangeapp_celery restart

echo
echo "Finished!"
