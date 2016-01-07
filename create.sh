COMPANY=orange
if [ ! -n "$1" ]; then
    echo "Syntax: create.sh project_name [company_name]"
    echo "Enter a project_name as first arguments"
    exit 1
fi
PROJECT=$1
if [ -n "$2" ]; then
    COMPANY=$2
fi

echo "Creating project dir ..."
mkdir -p $PROJECT-project
mkdir -p $PROJECT-project/$COMPANY/$PROJECT
cp -a LICENSE MANIFEST.in README.rst requirements.txt run.py setup.py $PROJECT-project
cp -a orange/__init__.py $PROJECT-project/$COMPANY
cp -a orange/myproject/* $PROJECT-project/$COMPANY/$PROJECT
cp -a utils $PROJECT-project/
mv $PROJECT-project/utils/myproject_nginx.conf $PROJECT-project/utils/$PROJECT"_nginx.conf"
mv $PROJECT-project/utils/uwsgi/myproject_panel.conf $PROJECT-project/utils/uwsgi/$PROJECT"_panel.conf"
mv $PROJECT-project/utils/uwsgi/myproject_uwsgi.ini $PROJECT-project/utils/uwsgi/$PROJECT"_uwsgi.ini"
cd $PROJECT-project

grep -rli 'myproject' * | xargs -i@ sed -i "s/myproject/$PROJECT/g" @
grep -rli 'orange' * | xargs -i@ sed -i "s/orange/$COMPANY/g" @
echo "+++ Created your project at $PROJECT-project"
echo "Creating your environment ..."
virtualenv env
./env/bin/pip install -r requirements.txt
echo "+++ Created your environment at env"

echo "Installing database ..."
CDR=`pwd`
env PYTHONPATH=$CDR ./env/bin/python $COMPANY/$PROJECT/scripts/database.py --install
echo "+++ Installed sqlite database in $PROJECT.db"
