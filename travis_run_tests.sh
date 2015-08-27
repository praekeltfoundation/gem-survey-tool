#!/bin/sh
python manage.py syncdb --all --noinput | tee
python manage.py migrate
python manage.py syncdb --migrate
coverage run --source=gems manage.py test