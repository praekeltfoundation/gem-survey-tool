#!/bin/bash
psql -c 'create extension if not exists hstore;' -d template1 -U postgres
psql -c 'create database gems;' -U postgres
psql -c 'create schema gems_reporting;' -U postgres
echo "DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql_psycopg2', 'NAME': 'gems', 'USER': 'postgres', 'PASSWORD': '', 'HOST': 'localhost', 'PORT': ''}}" > gems/local_settings.py
