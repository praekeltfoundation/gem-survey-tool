import datetime
from django.utils import timezone
from django.test import TestCase
import json
from django.test import Client
from gems.core.models import *

class RESTTestCase(TestCase):
    def test_save_data(self):
        c = Client()
        J = {
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
        result = c.post('/save_data/', content_type='application/json', data=json.dumps(J))
        self.assertEquals(Survey.objects.count(), 1)
        self.assertEquals(SurveyResult.objects.count(), 1)
        self.assertEquals(Contact.objects.count(), 1)