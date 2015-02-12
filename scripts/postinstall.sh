manage="${VENV}/bin/python ${INSTALLDIR}/${REPO}/manage.py"

su - postgres -c "createdb gems"
su - postgres -c "psql gems -c 'CREATE EXTENSION hstore;'"

$manage syncdb --noinput --no-initial-data --migrate
$manage collectstatic --noinput
