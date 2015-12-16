#! /bin/bash
if [ ! -n "$1" ]; then
    echo "Syntax: orangeapp_deploy branch_name"
    echo "Use \"master\" for default"
    exit 1
fi

service orangeapp_panel stop
sleep 1

if [ -f "/opt/orange/env/bin/pip" ]; then
    /opt/orange/env/bin/pip uninstall orangeapp -y
fi


mkdir -p /opt/orange/
chmod 777 -R /usr/local/orange/orangeapp/log/

rm -rf /opt/orange/orangeapp
git clone https://pprolancer@bitbucket.org/pprolancer/orangeapp.git -b $1 /opt/orange/orangeapp

virtualenv /opt/orange/env
cd /opt/orange/orangeapp
../env/bin/python setup.py install

#service postgresql restart

echo "+++ Running migration upgrade..."
# ../env/bin/orangeapp_db --upgrade

echo "+++ Running web server..."
service nginx restart
service orangeapp_panel start

echo
echo "Finished!"
