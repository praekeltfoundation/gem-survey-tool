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
                'user':{
                    'answers':{'age':'14'}
                },
                'contact':{
                    'extra':{
                        'age-1':'21',
                        'age':'xx',
                        'age-12':'rr',
                        'age-2':'21',
                        'age-3':'21',
                    },
                    'groups':[],
                    'subscription':{},
                    'key':'61a036aa272341c78c0d34b74092885e',
                    'surname': None,
                    'user_account':'8a410f412f0b4010ab88e1362518994f',
                    'bbm_pin': None,
                    'mxit_id': None,
                    'twitter_handle': None,
                    'wechat_id': None,
                    'email_address':None,
                    'facebook_id': None,
                    'msisdn':'+27822247336',
                    'gtalk_id': None,
                    'name': None,
                    'dob':None,
                    'created_at':'2015-02-25 07:19:39.505567',
                    '$VERSION':2
                },
                'conversation_key':'dbb13e9a55874a8d84165bde05c0ad52'
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