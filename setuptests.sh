#!/bin/bash
psql -c 'create database gems' -U postgres
psql gems -c 'create extension if not exists hstore' -U postgres
echo "DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql_psycopg2', 'NAME': 'gems', 'USER': 'postgres', 'PASSWORD': '', 'HOST': 'localhost', 'PORT': ''}}" > gems/local_settings.py
