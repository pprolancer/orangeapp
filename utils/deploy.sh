#! /bin/bash
if [ ! -n "$1" ]; then
    echo "Syntax: myproject_deploy branch_name"
    echo "Use \"master\" for default"
    exit 1
fi

service myproject_panel stop
sleep 1

if [ -f "/opt/orange/env/bin/pip" ]; then
    /opt/orange/env/bin/pip uninstall myproject -y
fi


mkdir -p /opt/orange/
chmod 777 -R /usr/local/orange/myproject/log/

rm -rf /opt/orange/myproject
git clone https://pprolancer@bitbucket.org/pprolancer/myproject.git -b $1 /opt/orange/myproject

virtualenv /opt/orange/env
cd /opt/orange/myproject
../env/bin/python setup.py install

#service postgresql restart

echo "+++ Running migration upgrade..."
# ../env/bin/myproject_db --upgrade

echo "+++ Running web server..."
service nginx restart
service myproject_panel start

echo
echo "Finished!"
