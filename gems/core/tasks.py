from __future__ import absolute_import
from celery import task
from gems.core.models import SurveyResult, ExportTypeMapping
from django.conf import settings
from django.db import connection
import logging
import json
import requests
from go_http.contacts import ContactsApiClient
from gems.core.models import Contact
from gems.core.viewhelpers import get_surveyresult_hstore_keys

logger = logging.getLogger(__name__)


def perform_casting(name, value):
    result = ExportTypeMapping.objects.filter(field__exact=name).first()

    if result:

        if result.cast == 1:
            # cast to int
            try:
                return int(value)
            except:
                pass

        elif result.cast == 2:
            # cast to float
            try:
                return float(value)
            except:
                pass

    return value


def process_results(result_set):
    results = []

    for sr in result_set:
        result = {
            'keys': ['id'],
            'id': sr.id,
            'survey': sr.survey.name,
            'contact': sr.contact.vkey,
            'created_at': sr.created_at.isoformat(),
            'updated_at': sr.updated_at.isoformat()
        }

        for key in sr.answer.keys():
            result[key] = perform_casting(name=key, value=sr.answer[key])

        results.append(result)

    return results


def fetch_results():
    try:
        raw_results = SurveyResult.objects.select_related().filter(sent=False)[:100]
    except Exception as ex:
        logger.error('export_data[Task]->fetch_results->DB failed: %s' % ex.message)
        raise

    try:
        processed_results = process_results(raw_results)
    except Exception as ex:
        logger.error('export_data[Task]->fetch_results->process failed: %s' % ex.message)
        raise

    return processed_results, raw_results.values('id')


def submit_results(sendable_results, raw_results):

    payload = json.dumps(sendable_results)

    url = settings.RJ_METRICS_URL + \
        settings.RJ_METRICS_CID + \
        '/table/' + \
        settings.RJ_METRICS_TABLE + \
        '/data'
    headers = {'Content-Type': 'application/json'}
    params = {'apikey': settings.RJ_METRICS_API_KEY}

    result = requests.post(
        url,
        headers=headers,
        params=params,
        data=payload
    )

    if result.status_code == 201:
        try:
            update_results(raw_results)
        except Exception as ex:
            logger.error(
                'export_data[Task]->submit_results->update_results failed: %s'
                % ex.message
            )
            raise
    else:
        logger.error(
            'export_data[Task]->submit_results failed: message: %s'
            % result.content
        )
        if result.status_code != 200:
            result.raise_for_status()


def update_results(results):
    SurveyResult.objects.filter(pk__in=results).update(sent=True)


@task(bind=True)
def export_data(self):

    logger.info('export_data[Task] :: Started')

    try:
        while True:
            pr, rr = fetch_results()

            # exit loop when all the rows have been submitted
            if len(rr) == 0:
                break

            submit_results(pr, rr)

    except Exception as ex:
        logger.error('export_data[Task] failed: %s' % ex.message)

    logger.info('export_data[Task] :: Completed')


@task(bind=True)
def import_contacts(self):

    logger.info('importing contacts :: Started')

    api = ContactsApiClient(settings.VUMI_TOKEN)

    all_contacts = list()
    try:
        for contact in api.contacts():
            all_contacts.append(contact)
    except Exception:
        logger.exception('importing contacts :: Failed to fetch contacts')

    count = 0
    try:
        for contact in all_contacts:
            contact, created = Contact.objects.get_or_create(msisdn=contact['msisdn'])
            if not created:
                continue
            contact.vkey = contact['key']
            contact.save()
            count += 1
    except Exception:
        logger.exception('creating contact :: Failed to create a contact %s' % contact['msisdn'])

    logger.info('%s contacts imported' % count)
    logger.info('importing contacts :: Completed')


@task
def construct_dashboard_survey_results_table():
    construct_summary_table_sql()


def construct_summary_table_sql():
    keys = get_surveyresult_hstore_keys(False)
    key_columns = ''

    for key in keys:
        if len(key_columns) > 0:
            key_columns += ', '

        key_columns += "answer->'%s' \"%s\"" % (key, key)

    sql = '''
    select s.survey_id, s.name "survey_name", s.series, s.created_on "survey_created_on",
      c.vkey "contact_vkey", %s, sr.created_at "result_created_on"
    into gems_reporting.dashboard_survey_results
    from core_surveyresult sr
      inner join core_survey s
        on s.survey_id = sr.survey_id
      inner join core_contact c
        on c.msisdn = sr.contact_id
    ''' % key_columns

    cursor = connection.cursor()

    cursor.execute('drop table if exists gems_reporting.dashboard_survey_results')
    cursor.execute(sql)
