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
pip uninstall myproject -y

mkdir -p /opt/orange/
mkdir -p /usr/local/orange/myproject/log/
chmod 777 -R /usr/local/orange/myproject/log/

rm -rf /opt/orange/myproject
git clone https://pprolancer@bitbucket.org/pprolancer/myproject.git -b $BRANCH /opt/orange/myproject

cp -a /opt/orange/myproject/utils/deploy.sh /usr/local/bin/myproject_deploy
cp /opt/orange/myproject/utils/myproject_nginx.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/myproject_nginx.conf /etc/nginx/sites-enabled/myproject_nginx.conf
cp /opt/orange/myproject/utils/uwsgi/myproject_panel.conf /etc/init/

virtualenv /opt/orange/env
cd /opt/orange/myproject
../env/bin/python setup.py install

echo "+++ Installing database..."
../env/bin/myproject_db --install

# restart services
echo "Restarting Server..."
service nginx restart
service myproject_panel restart

echo
echo "Finished!"
