GEMS
====

|gems-ci|_

.. |gems-ci| image:: https://travis-ci.org/praekelt/gem-survey-tool.svg?branch=develop
.. _gems-ci: https://travis-ci.org/praekelt/gem-survey-tool

Install
-------

::

    source ev/bin/active
    pip install -r requirements.txt
    ./manage.py syncdb --migrate

Tests
-----

Before running tests
~~~~~~~~~~~~~~~~~~~~

Configure your PostgreSQL db by running:

::

    psql -d template1 -c 'create extension hstore;'

Run Tests
~~~~~~~~~

./manage.py test
