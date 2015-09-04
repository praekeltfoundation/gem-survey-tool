#!/bin/sh
python manage.py syncdb --all --noinput | tee
coverage run --source=gems manage.py test