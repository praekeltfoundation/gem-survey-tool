#!/bin/sh
coverage run --source=gems manage.py test
coverage html --omit="gems/core/migrations/*"
firefox ./htmlcov/index.html&
