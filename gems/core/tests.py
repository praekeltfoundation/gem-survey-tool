import datetime
from django.utils import timezone
from django.test import TestCase
import json
from django.test import Client
from gems.core.models import *

class RESTTestCase(TestCase):
    def test_save_data(self):
        c = Client()
        j = {
            'user': {
                'answers': {
                    'choice-1': 'value-4'
                }
            },
            'contact': {
                'extra': {
                    'message-1': 'value-4',
                    'message-1-1': 'value-4'
                },
            'groups': [],
            'subscription': {},
            'msisdn': '+27123',
            'created_at': '2015-02-14 10:42:15.381',
            'user_account': 'ea689884-7867-48ee-17f0-ef3fb5f88127',
            'key': '7ee8c10c-8cba-4e6f-92c1-d3399f858f43',
            },
            'conversation_key': '1203491039401932804'
        }
        result = c.post('/save_data/', content_type='application/json', data=json.dumps(j))
        self.assertEquals(Survey.objects.count(), 1)
        self.assertEquals(SurveyResult.objects.count(), 1)
        self.assertEquals(Contact.objects.count(), 1)
        
    def test_csv_export(self):
        c = Client()
        j = {
            'filters': [
                {
                    'field': {
                        'name': 'age',
                        'type': 'H'
                    },
                    'filters': [
                        {
                            'operator': 'lt',
                            'value': '18'
                        },
                        {
                            'loperator': 'or',
                            'operator': 'gt',
                            'value': '12'
                        }
                    ]
                },
                {
                    'loperator': 'or',
                    'field': {
                        'name': 'Gender',
                        'type': 'H'
                    },
                    'filters': [
                        {
                            'operator': 'eq',
                            'value': 'female'
                        }
                    ]
                }
            ]
        }

        result = c.post('/export/', content_type='application/json', data=json.dumps(j))
        self.assertEquals(result._headers['content-type'][1], 'text/csv')
        self.assertEquals(result._headers['content-disposition'][1], 'attachment; filename=surveyresult_export.csv;')

        result = c.get('/export/')
        self.assertEquals(result._container[0], 'Bad request method')