from django.core.urlresolvers import reverse
import datetime
from django.utils import timezone
from django.test import TestCase
import json
from django.test import Client
from gems.core.models import *


class RESTTestCase(TestCase):
    def test_save_data(self):
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
        self.client.post('/save_data/', content_type='application/json', data=json.dumps(j))
        s = Survey.objects.all().first()
        sr = SurveyResult.objects.all().first()
        c = Contact.objects.all().first()
        self.assertIsNotNone(s)
        self.assertIsNotNone(sr)
        self.assertIsNotNone(c)
        self.assertEquals(sr.answer["age"], "14")
        self.assertEquals(s.name, "New Survey - Please update")
        self.assertEquals(c.msisdn, "+27822247336")

        resp = self.client.get('/save_data/')
        self.assertContains(resp, '{"status": "Failed"}')

    def test_csv_export(self):
        result = self.client.get(path='/export_survey/', data={"pk": "1"})
        self.assertEquals(result._headers['content-type'][1], 'text/csv')
        self.assertEquals(result._headers['content-disposition'][1], 'attachment; filename=1_survey_results.csv;')

        result = self.client.post(path='/export_survey/')
        self.assertContains(result, 'Bad request method')

        result = self.client.post(path='/export_survey_results/')
        self.assertContains(result, 'Bad request method')

        result = self.client.get(path='/export_survey_results/', data={"rows": "[1,2,3]"})
        self.assertEquals(result._headers['content-type'][1], 'text/csv')
        self.assertEquals(result._headers['content-disposition'][1], 'attachment; filename=surveyresult_export.csv;')


class GeneralTests(TestCase):
    def test_login(self):
        usr = User.objects.create_user("admin", "admin@admin.com", "admin")

        resp = self.client.get(reverse('login'))
        self.assertContains(resp, "Sign in")

        resp = self.client.post(reverse('login'),
                                data={
                                    'username': "a",
                                    'password': "a"
                                },
                                follow=True)
        self.assertContains(resp, "*Username and password combination incorrect")

        usr.is_active = False
        usr.save()
        resp = self.client.post(reverse('login'),
                                data={
                                    'username': "admin",
                                    'password': "admin"
                                },
                                follow=True)
        self.assertContains(resp, "*Your account has been disabled")

        usr.is_active = True
        usr.save()
        resp = self.client.post(reverse('login'),
                                data={
                                    'username': "admin",
                                    'password': "admin"
                                },
                                follow=True)
        self.assertContains(resp, "Admin..")

        resp = self.client.get(reverse('logout'))
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(resp.url, "http://testserver/login")

    def test_contact_groups(self):
        resp = self.client.get("/contact-groups/")
        # TODO: Complete Test

    def test_build_query(self):
        resp = self.client.get("/build_query/")
        # TODO: Complete Test

    def test_query(self):
        resp = self.client.get("/query/")
        # TODO: Complete Test

    def test_home(self):
        resp = self.client.get("/home/")
        # TODO: Complete Test

    def test_contactgroup(self):
        resp = self.client.get("/contactgroup/")
        # TODO: Complete Test

    def test_delete_contact_group(self):
        resp = self.client.get("/delete_contactgroup/")
        # TODO: Complete Test

    def test_create_contact_group(self):
        resp = self.client.get("/create_contactgroup/")
        # TODO: Complete Test

    def test_update_contact_group(self):
        resp = self.client.get("/update_contactgroup/")
        # TODO: Complete Test

    def test_get_surveys(self):
        resp = self.client.get("/get_surveys/")
        # TODO: Complete Test

    def test_get_uique_keys(self):
        resp = self.client.get("/get_unique_keys/")
        # TODO: Complete Test


class TaskTests(TestCase):
    def test_rj_metrics_task(self):
        pass
        # TODO: Complete Tests
