from __future__ import absolute_import
from celery import task


@task(bind=True)
def export_data(self):
    return 42