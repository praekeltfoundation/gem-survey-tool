from __future__ import absolute_import
from celery import task
from gems.core.models import SurveyResult
import logging

logger = logging.getLogger(__name__)


def process_results(result_set):
    results = []

    for sr in result_set:
        result = {
            'keys': ['id'],
            'id': sr.id,
            'survey': sr.survey.name,
            'contact': sr.contact.vkey,
            'created_at': str(sr.created_at),
            'updated_at': str(sr.updated_at)
        }

        for key in sr.answer.keys():
            result[key] = sr.answer[key]

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
    # todo: send the data to rj metrics
    result = 201

    if result == 201:
        try:
            update_results(raw_results)
        except Exception as ex:
            logger.error('export_data[Task]->submit_results->update_results failed: %s' % ex.message)
            raise


def update_results(results):
    SurveyResult.objects.filter(pk__in=results).update(sent=True)


#@task(bind=True)
def export_data():

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