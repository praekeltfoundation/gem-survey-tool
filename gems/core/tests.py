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
        c.post('/save_data/', content_type='application/json', data=json.dumps(j))
        s = Survey.objects.all().first()
        sr = SurveyResult.objects.all().first()
        c = Contact.objects.all().first()
        self.assertIsNotNone(s)
        self.assertIsNotNone(sr)
        self.assertIsNotNone(c)
        self.assertEquals(sr.answer["age"], "14")
        self.assertEquals(s.name, "New Survey - Please update")
        self.assertEquals(c.msisdn, "+27822247336")
        
    def test_csv_export(self):
        c = Client()
        result = c.get(path='/export_survey/', data={"pk": "1"})
        self.assertEquals(result._headers['content-type'][1], 'text/csv')
        self.assertEquals(result._headers['content-disposition'][1], 'attachment; filename=1_survey_results.csv;')

        result = c.post(path='/export_survey/')
        self.assertContains(result, 'Bad request method')

        result = c.post(path='/export_survey_results/')
        self.assertContains(result, 'Bad request method')

        result = c.get(path='/export_survey_results/', data={"rows": "[1,2,3]"})
        self.assertEquals(result._headers['content-type'][1], 'text/csv')
        self.assertEquals(result._headers['content-disposition'][1], 'attachment; filename=surveyresult_export.csv;')
