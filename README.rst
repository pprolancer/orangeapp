Orange App
========

Orange App is a blank structure for a web service using Rest API + Flask + sqlalchemy.
you can use a clone of this project to start your new project.


Directory Structure
-------------------

The following root folders are know to this project at the moment:

* orange: package containing back-end code and apis.

* utils: any conf files and additional files which may we need for installation


Create yourself project
-----------------------

.. code:: sh

    $ git clone https://github.com/pprolancer/orangeapp.git
    $ cd orangeapp
    $ ./create.sh your_project your_company
    $ mv ./your_project-project to_your_workspace
    $ cd to_your_workspace/your_project-project
    $ run env PYTHONPATH=to_your_workspace/your_project-project ./env/bin/python run.py
    $ open http://localhost:5001 on browser
    $ open http://localhost:5001/api/v1/session on browser with username: admin and password: test1234

