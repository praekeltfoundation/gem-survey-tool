# GEMS

## Install
```
source ev/bin/active
pip install -r requirements.txt
./manage.py syncdb --migrate
```

## Tests
### Before running tests
Configure your PostgreSQL db by running: 
```
psql -d template1 -c 'create extension hstore;'
```

### Run Tests
./manage.py test
