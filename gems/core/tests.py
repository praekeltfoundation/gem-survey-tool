from django.core.urlresolvers import reverse
from datetime import datetime
from django.utils import timezone
from django.test import TestCase
import json
from django.test import Client
from gems.core.models import *
from mock import patch
from csv_utils import process_header, process_line, split_line, survey_lookup, process_file
import os


class RESTTestCase(TestCase):
    def setUp(self):
        self.j = {
            'user': {
                'answers': {'age': '14'}
            },
            'contact': {
                'extra': {
                    'age-1': '21',
                    'age': 'xx',
                    'age-12': 'rr',
                    'age-2': '21',
                    'age-3': '21'
                },
                'groups': [],
                'subscription': {},
                'key': '61a036aa272341c78c0d34b74092885e',
                'surname': None,
                'user_account': '8a410f412f0b4010ab88e1362518994f',
                'bbm_pin': None,
                'mxit_id': None,
                'twitter_handle': None,
                'wechat_id': None,
                'email_address': None,
                'facebook_id': None,
                'msisdn': '+27822247336',
                'gtalk_id': None,
                'name': None,
                'dob': None,
                'created_at': '2015-02-25 07:19:39.505567',
                '$VERSION': 2
            },
            'conversation_key': 'dbb13e9a55874a8d84165bde05c0ad52'
        }

    def test_save_data(self):

        resp = self.client.post('/save_data/', content_type='application/json', data=json.dumps(self.j))
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

    def test_save_data_multiple_responses(self):
        self.client.post('/save_data/', content_type='application/json', data=json.dumps(self.j))

        # change age to test update
        self.j["user"]["answers"]["age"] = 22

        self.client.post('/save_data/', content_type='application/json', data=json.dumps(self.j))
        sr = SurveyResult.objects.all().first()
        self.assertEquals(sr.answer["age"], u"22")

        # add color to test merge
        self.j["user"]["answers"]["color"] = "red"

        self.client.post('/save_data/', content_type='application/json', data=json.dumps(self.j))
        sr = SurveyResult.objects.all().first()
        self.assertEquals(sr.answer["age"], u"22")
        self.assertEquals(sr.answer["color"], "red")

        # remove age to test reservation
        self.j["user"]["answers"].pop("color", None)
        self.client.post('/save_data/', content_type='application/json', data=json.dumps(self.j))
        qs = SurveyResult.objects.all()
        cnt = qs.count()
        self.assertEquals(cnt, 1)
        sr = qs.first()
        self.assertEquals(sr.answer["age"], u"22")
        self.assertEquals(sr.answer["color"], "red")

        cnt = RawSurveyResult.objects.all().count()
        self.assertEquals(cnt, 4)

        cnt = IncomingSurvey.objects.all().count()
        self.assertEquals(cnt, 4)

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

    def create_survey(self, survey_id="0928309402384908203423", name="Test"):
        return Survey.objects.create(
            name=name,
            survey_id=survey_id
        )

    def create_contact(self, msisdn="123456789", vkey="234598274987l"):
        return Contact.objects.create(
            msisdn=msisdn,
            vkey=vkey
        )

    def create_survey_result(self, survey, contact, answers):
        return SurveyResult.objects.create(
            survey=survey,
            contact=contact,
            answer=answers
        )

    def setUp(self):
        self.f = {
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

        self.survey = self.create_survey()
        self.contact = self.create_contact()

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
        User.objects.create_user("admin", "admin@admin.com", "admin")

        self.client.post(reverse('login'),
                         {
                             'username': "admin",
                             'password': "admin"
                         },
                         follow=True)

        resp = self.client.get(reverse("contactgroups"))
        self.assertEquals(resp.status_code, 200)

    def test_query(self):
        resp = self.client.post("/query/", content_type='application/json', data=json.dumps(self.f))
        self.assertContains(resp, "[]")

        self.create_survey_result(survey=self.survey, contact=self.contact, answers={"age": 21, "color": "redish"})
        resp = self.client.post("/query/", content_type='application/json', data=json.dumps(self.f))
        self.assertContains(resp, "redish")

    def test_home(self):
        resp = self.client.get("/home/")
        self.assertEquals(resp.status_code, 200)

    def test_contactgroup(self):
        resp = self.client.get("/contactgroup/")
        self.assertEquals(resp.status_code, 200)

    def test_delete_contact_group(self):
        resp = self.client.get("/delete_contactgroup/")
        # TODO: Complete Test

    def fake_create_group(self, name):
        return {'key': 'abc', 'filters': "{'a':'a', 'b':'b'}", 'query_words': 'age > 20'}

    def fake_process_group_member(api, member, contact_group ):
        pass

    @patch('gems.core.views.process_group_member', fake_process_group_member)
    @patch('go_http.contacts.ContactsApiClient.create_group', fake_create_group)
    def test_create_contact_group(self):
        User.objects.create_user("admin", "admin@admin.com", "admin")

        self.client.post(reverse('login'),
                         {
                             'username': "admin",
                             'password': "admin"
                         },
                         follow=True)

        resp = self.client.get("/create_contactgroup/")
        self.assertContains(resp, "FAILED")

        resp = self.client.post('/create_contactgroup/',
                                data='{"name": "group name", "filters": "filter", "query_words": '
                                     '"age > 20", "members": "members"}',
                                content_type="application/json",
                                follow=True)
        group = ContactGroup.objects.all().first()

        self.assertEquals(u'group name', group.name)
        self.assertEquals(u'filter', group.filters)
        self.assertEquals(u'age > 20', group.query_words)
        self.assertEquals(resp.content, "OK")

    def test_update_contact_group(self):
        resp = self.client.get("/update_contactgroup/")
        self.assertContains(resp, "FAILED")

        User.objects.create_user("admin", "admin@admin.com", "admin")

        self.client.post(reverse('login'),
                         {
                             'username': "admin",
                             'password': "admin"
                         },
                         follow=True)

        mock_create_group = patch('ContactsAPIClient.update_group')
        r = {'key': 'abc', 'filters': "{'a':'a', 'b':'b'}", 'query_words': 'age > 20'}
        mock_create_group.return_value = r

        patch('gems.core.views.process_group_member')
        patch('gems.core.views.remove_group_member')


        # TODO: Complete Test

    def test_get_surveys(self):
        resp = self.client.get("/get_surveys/")
        self.assertContains(resp, "FAILED")

        self.create_survey_result(self.survey, self.contact, {"age": 21})

        resp = self.client.post(
            "/get_surveys/",
            content_type='application/json',
            data=json.dumps(
                {
                    "name": "Test",
                    "from": "2015/01/01",
                    "to": "2015/12/31"
                }
            )
        )

        self.assertContains(resp, "0928309402384908203423")

    def test_get_unique_keys(self):
        resp = self.client.get("/get_unique_keys/")
        # TODO: Complete Test


class ModelTests(TestCase):
    def test_incoming_survey_length_limit(self):
        j={
            "test": ""
        }

        t = ""

        for i in range(0, 2000):
            t += "1"

        j["test"] = t + "TEST"
        t = json.dumps(j)[:2000]

        self.client.post('/save_data/', content_type='application/json', data=json.dumps(j))
        ins = IncomingSurvey.objects.all().first()
        self.assertEquals(ins.raw_message, t)


class TaskTests(TestCase):
    def test_rj_metrics_task(self):
        pass
        # TODO: Complete Tests


class CsvImportTests(TestCase):
    def test_process_headers(self):
        header_line = "survey, survey_key, msisdn, key, timestamp"

        parts = split_line(header_line)
        self.assertIsNotNone(parts)
        self.assertEquals(len(parts), 5)

        header_map, survey_index, survey_key_index, contact_index, contact_key_index, date_index = process_header(parts)

        self.assertIsNotNone(header_map)
        self.assertIsNotNone(survey_index)
        self.assertIsNotNone(survey_key_index)
        self.assertIsNotNone(contact_index)
        self.assertIsNotNone(contact_key_index)
        self.assertIsNotNone(date_index)

        self.assertEquals(survey_index, 0)
        self.assertEquals(survey_key_index, 1)
        self.assertEquals(contact_index, 2)
        self.assertEquals(contact_key_index, 3)
        self.assertEquals(date_index, 4)

        self.assertEquals(header_map["survey"], 0)
        self.assertEquals(header_map["msisdn"], 2)

        # shuffle the keys
        header_line = "msisdn, survey, survey_key, timestamp, key"

        parts = split_line(header_line)
        self.assertIsNotNone(parts)
        self.assertEquals(len(parts), 5)

        header_map, survey_index, survey_key_index, contact_index, contact_key_index, date_index = process_header(parts)

        self.assertIsNotNone(header_map)
        self.assertIsNotNone(survey_index)
        self.assertIsNotNone(survey_key_index)
        self.assertIsNotNone(contact_index)
        self.assertIsNotNone(contact_key_index)
        self.assertIsNotNone(date_index)

        self.assertEquals(survey_index, 1)
        self.assertEquals(survey_key_index, 2)
        self.assertEquals(contact_index, 0)
        self.assertEquals(contact_key_index, 4)
        self.assertEquals(date_index, 3)

        self.assertEquals(header_map["survey"], 1)
        self.assertEquals(header_map["msisdn"], 0)

    def test_process_line(self):
        header_line = "survey, survey_key, msisdn, key, timestamp, age, color"
        data_line = "Test Survey, 029830492039, 27801231234, 093450934, 2015-03-27T12:08:55.032231, 24, red"

        parts = split_line(header_line)
        header_map, survey_index, survey_key_index, contact_index, contact_key_index, date_index = process_header(parts)
        headers = parts

        parts = split_line(data_line)
        result, error = process_line(survey_index, survey_key_index, contact_index, contact_key_index, date_index, header_map, headers, parts)

        self.assertEquals(result, 1)
        self.assertEquals(error, None)

        survey = Survey.objects.get(name__exact="Test Survey")
        contact = Contact.objects.get(msisdn__exact="27801231234")
        sr = SurveyResult.objects.get(survey=survey, contact=contact)

        self.assertEquals(sr.answer["age"], "24")
        self.assertEquals(sr.answer["color"], "red")

        # shuffle the keys
        header_line = "msisdn, survey, survey_key, timestamp, age, color, key"
        data_line = "27801231244, Test Survey, 029830492039, 2015-03-27T12:08:55.032231, 24, red, 093450934"

        parts = split_line(header_line)
        header_map, survey_index, survey_key_index, contact_index, contact_key_index, date_index = process_header(parts)
        headers = parts

        parts = split_line(data_line)
        result, error = process_line(survey_index, survey_key_index, contact_index, contact_key_index, date_index, header_map, headers, parts)

        self.assertEquals(result, 1)
        self.assertEquals(error, None)

        survey = Survey.objects.get(name__exact="Test Survey")
        contact = Contact.objects.get(msisdn__exact="27801231244")
        sr = SurveyResult.objects.get(survey=survey, contact=contact)

        self.assertEquals(sr.answer["age"], "24")
        self.assertEquals(sr.answer["color"], "red")
        self.assertEquals(sr.created_at.date(), datetime(2015, 03, 27).date())

        # test more data rows than headers
        header_line = "survey, survey_key, msisdn, key, timestamp"
        data_line = "Test Survey, 029830492039, 27801231234, 093450934, 2015-03-27T12:08:55.032231, 24, red"
        headers = split_line(header_line)
        header_map, survey_index, survey_key_index, contact_index, contact_key_index, date_index = process_header(headers)
        parts = split_line(data_line)
        result, error = process_line(survey_index, survey_key_index, contact_index, contact_key_index, date_index, header_map, headers, parts)

        self.assertEquals(result, 0)
        self.assertEquals(error, "list index out of range")

        # test not all required fields are present, ie. no answers
        header_line = "survey, survey_key, msisdn, key, timestamp"
        data_line = "Test Survey, 029830492039, 27801231234, 093450934, 2015-03-27T12:08:55.032231"
        headers = split_line(header_line)
        header_map, survey_index, survey_key_index, contact_index, contact_key_index, date_index = process_header(headers)
        parts = split_line(data_line)
        result, error = process_line(survey_index, survey_key_index, contact_index, contact_key_index, date_index, header_map, headers, parts)

        self.assertEquals(result, 0)
        self.assertEquals(error, "Survey, Contact and at least 1 answer is required")

        # split_line none line check
        self.assertIsNone(split_line(None))

        # survey_lookup none key lookup test
        self.assertIsNotNone(survey_lookup("Test Survey", None))

    def test_process_file(self):
        filename = "/tmp/tmp_tmp_tmp_tmp"
        fout = open(filename, "w")
        fout.write("survey, survey_key, msisdn, key, timestamp, age, color\n")
        fout.write("Test Survey, 029830492039, 27801231234, 093450934, 2015-03-27T12:08:55.032231, 24, red\n")
        fout.close()

        errors, num_rows = process_file(filename)

        self.assertEquals(len(errors), 0)
        self.assertEquals(num_rows, 2)

        survey = Survey.objects.get(name__exact="Test Survey")
        contact = Contact.objects.get(msisdn__exact="27801231234")
        sr = SurveyResult.objects.get(survey=survey, contact=contact)

        self.assertEquals(sr.answer["age"], "24")
        self.assertEquals(sr.answer["color"], "red")

        os.remove(filename)

        # test errors
        fout = open(filename, "w")
        fout.write("survey, survey_key, msisdn, key, timestamp\n")
        fout.write("Test Survey, 029830492039, 27801231234, 093450934, 2015-03-27T12:08:55.032231, 24, red\n")
        fout.close()

        errors, num_rows = process_file(filename)

        self.assertEquals(len(errors), 1)
        self.assertEquals(errors[0]["row"], 2)
        self.assertEquals(errors[0]["error"], "list index out of range")
        self.assertEquals(num_rows, 2)

        os.remove(filename)

        # test num result created
        fout = open(filename, "w")
        fout.write("survey, survey_key, msisdn, key, timestamp, age, color\n")
        for i in range(0, 100):
            fout.write("Test Survey, 029830492039, 27801231233, 093450933, 2015-03-27T12:08:55.032231, %s, red\n" % i)
        fout.close()

        errors, num_rows = process_file(filename)

        self.assertEquals(len(errors), 0)
        self.assertEquals(num_rows, 101)

        survey = Survey.objects.get(name__exact="Test Survey")
        contact = Contact.objects.get(msisdn__exact="27801231233")
        cnt = SurveyResult.objects.filter(survey=survey, contact=contact).count()

        self.assertEquals(cnt, 100)

        os.remove(filename)