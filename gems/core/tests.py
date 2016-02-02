# coding: UTF-8

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test import Client
from django.db import connection
from gems.core.models import Contact, ContactGroup, ContactGroupMember, Survey, SurveyResult, RawSurveyResult, \
    IncomingSurvey, User, Setting
from gems.core.tasks import construct_summary_table_sql
from mock import patch
from csv_utils import process_header, process_line, split_line, survey_lookup, process_file
from datetime import datetime
import os
import json
import random
from django.conf import settings
from celery import current_app
from django.db.models.manager import Manager


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

    def test_rest_pages_empty(self):
        result = self.client.get(path="/survey/")
        self.assertContains(result, "\"count\":0")

        result = self.client.get(path="/surveyresult/")
        self.assertContains(result, "\"count\":0")

        result = self.client.get(path="/contact/")
        self.assertContains(result, "\"count\":0")

        result = self.client.get(path="/contactgroup/")
        self.assertContains(result, "\"count\":0")

        result = self.client.get(path="/contactgroupmember/")
        self.assertContains(result, "\"count\":0")

    def test_rest_pages_empty_params(self):
        result = self.client.get(path="/survey/?page=1&page_size=100")
        self.assertContains(result, "\"count\":0")

        result = self.client.get(path="/surveyresult/?page=1&page_size=100")
        self.assertContains(result, "\"count\":0")

        result = self.client.get(path="/contact/?page=1&page_size=100")
        self.assertContains(result, "\"count\":0")

        result = self.client.get(path="/contactgroup/?page=1&page_size=100")
        self.assertContains(result, "\"count\":0")

        result = self.client.get(path="/contactgroupmember/?page=1&page_size=100")
        self.assertContains(result, "\"count\":0")

    def test_rest_pages_empty_params_errors(self):
        result = self.client.get(path="/survey/?page=2&page_size=100")
        self.assertContains(result, "Invalid page", status_code=404)

        result = self.client.get(path="/surveyresult/?page=2&page_size=100")
        self.assertContains(result, "Invalid page", status_code=404)

        result = self.client.get(path="/contact/?page=2&page_size=100")
        self.assertContains(result, "Invalid page", status_code=404)

        result = self.client.get(path="/contactgroup/?page=2&page_size=100")
        self.assertContains(result, "Invalid page", status_code=404)

        result = self.client.get(path="/contactgroupmember/?page=2&page_size=100")
        self.assertContains(result, "Invalid page", status_code=404)

    def test_rest_pages(self):
        s = Survey.objects.create(survey_id="123", name="test")
        result = self.client.get(path="/survey/")
        self.assertContains(result, "\"count\":1")
        self.assertContains(result, "\"name\":\"test\"")

        c = Contact.objects.create(msisdn="+27821230000", vkey="1234")
        result = self.client.get(path="/contact/")
        self.assertContains(result, "\"count\":1")
        self.assertContains(result, "\"vkey\":\"1234\"")

        SurveyResult.objects.create(survey=s, contact=c, answer={"age": "21"})
        result = self.client.get(path="/surveyresult/")
        self.assertContains(result, "\"count\":1")
        self.assertContains(result, "\"name\":\"test\"")
        self.assertContains(result, "\"vkey\":\"1234\"")

        result = self.client.get(path="/rawsurveyresult/")
        self.assertContains(result, "\"name\":\"test\"")
        self.assertContains(result, "\"vkey\":\"1234\"")

        usr = User.objects.create_user("admin", "admin@admin.com", "admin")
        cg = ContactGroup.objects.create(group_key="1234", name="test group", created_by=usr)
        result = self.client.get(path="/contactgroup/")
        self.assertContains(result, "\"count\":1")
        self.assertContains(result, "\"name\":\"test group\"")
        self.assertContains(result, "\"group_key\":\"1234\"")

        ContactGroupMember.objects.create(group=cg, contact=c)
        result = self.client.get(path="/contactgroupmember/")
        self.assertContains(result, "\"count\":1")
        self.assertContains(result, "\"name\":\"test group\"")
        self.assertContains(result, "\"group_key\":\"1234\"")


class GeneralTests(TestCase):

    def create_survey(self, survey_id="0928309402384908203423", name="Test", series="1"):
        return Survey.objects.create(
            name=name,
            survey_id=survey_id,
            series=series
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

    def create_contact_group(self, group_key, name, created_by, filters='filter', query_words='query_words'):
        return ContactGroup.objects.create(group_key=group_key, name=name, created_by=created_by, filters=filters,
                                           query_words=query_words)

    def create_contact_group_member(self, group, contact):
        return ContactGroupMember.objects.create(group=group, contact=contact)

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

        settings.CELERY_ALWAYS_EAGER = True
        current_app.conf.CELERY_ALWAYS_EAGER = True

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

    @patch('gems.core.views.ContactsApiClient.delete_group')
    def test_delete_contact_group(self, fake_delete_contact):
        # create user and login
        user = User.objects.create_user("admin", "admin@admin.com", "admin")
        self.client.post(reverse('login'),
                         {
                             'username': "admin",
                             'password': "admin"
                         },
                         follow=True)

        group_key = 'asdfg'
        group_name = 'group_1'
        contact_group = self.create_contact_group(group_key, group_name, user)
        contact = self.create_contact('+270911234567', '12345679123456')
        self.create_contact_group_member(contact_group, contact)

        resp = self.client.get(reverse('group.delete'))
        self.assertContains(resp, "Bad Request!", status_code=400)

        # post call with no data passed or invalid json
        resp = self.client.post(reverse('group.delete'),
                                data={},
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        resp = self.client.post(reverse('group.delete'),
                                data={'{group_key:'},
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        # post call with no group name passed
        resp = self.client.post(reverse('group.delete'),
                                data='{"group_key": ""}',
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        # wrong group key
        resp = self.client.post(reverse('group.delete'),
                                data='{"group_key": "147852"}',
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        #exception
        fake_delete_contact.side_effect = Exception
        resp = self.client.post(reverse('group.delete'),
                                data='{"group_key": "%s"}' % group_key,
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)
        count = ContactGroup.objects.all().count()
        self.assertEquals(count, 1)
        fake_delete_contact.side_effect = None

        #group_keys not matching
        fake_delete_contact.return_value = {'key': '135468'}
        resp = self.client.post(reverse('group.delete'),
                                data='{"group_key": "%s"}' % group_key,
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)
        count = ContactGroup.objects.all().count()
        self.assertEquals(count, 1)
        count = ContactGroupMember.objects.all().count()
        self.assertEquals(count, 1)

        #valid
        fake_delete_contact.return_value = {'key': group_key}
        resp = self.client.post(reverse('group.delete'),
                                data='{"group_key": "%s"}' % group_key,
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Contact group deleted!')
        count = ContactGroup.objects.all().count()
        self.assertEquals(count, 0)
        count = ContactGroupMember.objects.all().count()
        self.assertEquals(count, 0)

    @patch('gems.core.views.ContactsApiClient.update_contact')
    @patch('gems.core.views.ContactsApiClient.get_contact')
    @patch('gems.core.views.ContactsApiClient.create_group')
    def test_create_contact_group(self, fake_create_group, fake_get_contact, fake_update_contact):
        # create user and login
        User.objects.create_user("admin", "admin@admin.com", "admin")
        self.client.post(reverse('login'),
                         {
                             'username': "admin",
                             'password': "admin"
                         },
                         follow=True)

        # get call
        resp = self.client.get(reverse('group.create'))
        self.assertContains(resp, "Bad Request!", status_code=400)

        # post call with no data passed or invalid json
        resp = self.client.post(reverse('group.create'),
                                data={},
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        resp = self.client.post(reverse('group.create'),
                                data={'{name:'},
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        # post call with no group name passed
        resp = self.client.post(reverse('group.create'),
                                data='{"name": ""}',
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        # post with valid data with no members passed
        group_name = 'group_1'
        filter_words = 'filter'
        query_words = 'age > 20'
        fake_create_group.return_value = {'key': '%sabc' % group_name, 'filters': "{'a':'a', 'b':'b'}",
                                          'query_words': 'age > 20', 'name': group_name}

        resp = self.client.post('/create_contactgroup/',
                                data='{"name": "%s", "filters": "%s", "query_words": "%s"}' % (group_name, filter_words,
                                                                                               query_words),
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Contact group %s successfully created.' % group_name)
        group = ContactGroup.objects.get(name=group_name)
        self.assertEquals(group_name, group.name)
        self.assertEquals(filter_words, group.filters)
        self.assertEquals(query_words, group.query_words)

        # post - contact not found in vumi
        group_name = 'group_2'
        filter_words = 'filter 2'
        query_words = 'gender = male'
        fake_create_group.return_value = {'key': '%sabc' % group_name, 'filters': "{'a':'a', 'b':'b'}",
                                          'query_words': 'age > 20', 'name': group_name}

        member_1 = self.create_contact('+27701234567', vkey='')
        member_2 = '+270801234567'

        fake_get_contact.side_effect = Exception
        resp = self.client.post('/create_contactgroup/',
                                data='{"name": "%s", "filters": "%s", "query_words": "%s", "members": '
                                     '[{"value": "%s"}, {"value": "%s"}]''}' %
                                     (group_name, filter_words, query_words, member_1.msisdn, member_2),
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Contact group %s successfully created.' % group_name)
        group = ContactGroup.objects.get(name=group_name)
        self.assertEquals(group_name, group.name)
        self.assertEquals(filter_words, group.filters)
        self.assertEquals(query_words, group.query_words)
        count = ContactGroupMember.objects.all().count()
        self.assertEquals(count, 0)

        # post update failed
        group_name = 'group_3'
        filter_words = 'filter 3'
        query_words = 'gender = female'
        fake_create_group.return_value = {'key': '%sabc' % group_name, 'filters': "{'a':'a', 'b':'b'}",
                                          'query_words': 'age > 20', 'name': group_name}

        fake_get_contact.side_effect = None
        fake_get_contact.return_value = {'key': 'abcde'}
        fake_update_contact.side_effect = Exception
        resp = self.client.post('/create_contactgroup/',
                                data='{"name": "%s", "filters": "%s", "query_words": "%s", "members": '
                                     '[{"value": "%s"}, {"value": "%s"}]''}' %
                                     (group_name, filter_words, query_words, member_1.msisdn, member_2),
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Contact group %s successfully created.' % group_name)
        group = ContactGroup.objects.get(name=group_name)
        self.assertEquals(group_name, group.name)
        self.assertEquals(filter_words, group.filters)
        self.assertEquals(query_words, group.query_words)
        count = ContactGroupMember.objects.filter(synced=False).count()
        self.assertEquals(count, 1)

        # #post - updated
        group_name = 'group_4'
        filter_words = 'filter 4'
        query_words = 'age > 30'
        fake_create_group.return_value = {'key': '%sabc' % group_name, 'filters': "{'a':'a', 'b':'b'}",
                                          'query_words': 'age > 20', 'name': group_name}
        fake_update_contact.side_effect = None
        resp = self.client.post('/create_contactgroup/',
                                data='{"name": "%s", "filters": "%s", "query_words": "%s", "members": '
                                     '[{"value": "%s"}, {"value": "%s"}]''}' %
                                     (group_name, filter_words, query_words, member_1.msisdn, member_2),
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Contact group %s successfully created.' % group_name)
        group = ContactGroup.objects.get(name=group_name)
        self.assertEquals(group_name, group.name)
        self.assertEquals(filter_words, group.filters)
        self.assertEquals(query_words, group.query_words)
        count = ContactGroupMember.objects.filter(synced=False).count()
        self.assertEquals(count, 1)

        with patch.object(Manager, 'get_or_create') as mock_method:
            mock_method.side_effect = Exception("test error")

            group_name = 'group_5'
            filter_words = 'filter 4'
            query_words = 'age > 30'
            fake_create_group.return_value = {'key': '%sabc' % group_name, 'filters': "{'a':'a', 'b':'b'}",
                                              'query_words': 'age > 20', 'name': group_name}
            fake_update_contact.side_effect = None
            resp = self.client.post('/create_contactgroup/',
                                    data='{"name": "%s", "filters": "%s", "query_words": "%s", "members": '
                                         '[{"value": "%s"}, {"value": "%s"}]''}' %
                                         (group_name, filter_words, query_words, member_1.msisdn, member_2),
                                    content_type="application/json",
                                    follow=True)
            self.assertContains(resp, 'Contact group %s successfully created.' % group_name)
            group = ContactGroup.objects.get(name=group_name)
            self.assertEquals(group_name, group.name)
            self.assertEquals(filter_words, group.filters)
            self.assertEquals(query_words, group.query_words)
            count = ContactGroupMember.objects.filter(synced=False).count()
            self.assertEquals(count, 1)

    @patch('gems.core.views.ContactsApiClient.update_contact')
    @patch('gems.core.views.ContactsApiClient.get_contact')
    @patch('gems.core.views.ContactsApiClient.update_group')
    def test_update_contact_group(self, fake_update_group, fake_get_contact, fake_update_contact):
        user = User.objects.create_user("admin", "admin@admin.com", "admin")

        self.client.post(reverse('login'),
                         {
                             'username': "admin",
                             'password': "admin"
                         },
                         follow=True)

        # get call
        resp = self.client.get(reverse('group.update'))
        self.assertContains(resp, 'Bad Request!', status_code=400)

        # post call with no data passed or invalid json
        resp = self.client.post(reverse('group.update'),
                                data={},
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        resp = self.client.post(reverse('group.update'),
                                data={'{group_key:'},
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        # no group key
        resp = self.client.post(reverse('group.update'),
                                data='{group_key: ""}',
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        # valid post
        group_key = 'asdf'
        group_name = 'funky'
        new_name = 'dinky'
        filters = 'filters'
        query_words = 'age < 18'
        contact_group = self.create_contact_group(group_key, group_name, user)
        existing_contact_1 = self.create_contact('+27711234567', vkey='')
        self.create_contact_group_member(contact_group, existing_contact_1)
        existing_contact_2 = self.create_contact('+27711234566', '1234566788')
        self.create_contact_group_member(contact_group, existing_contact_2)
        new_contact = self.create_contact('+27711234565', '1234566787')


        # exception
        fake_get_contact.side_effect = Exception
        resp = self.client.post(reverse('group.update'),
                                data='{"group_key": "%s", "name": "%s", "filters": "%s", "query_words": "%s", '
                                     '"members": [{"value": "%s"}, {"value": "%s"}, {"value": "+123456789"}]''}'
                                     % (group_key, new_name, filters, query_words, existing_contact_2, new_contact),
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Contact group details updated. Group members will be updated shortly.')
        count = ContactGroupMember.objects.filter(group=contact_group).count()
        self.assertEquals(count, 3)

        #update exception
        fake_update_contact.side_effect = Exception
        g_list = list()
        g_list.append(group_key)
        fake_get_contact.return_value = {'key': 'abcde', 'groups': g_list}
        fake_get_contact.side_effect = None
        resp = self.client.post(reverse('group.update'),
                                data='{"group_key": "%s", "name": "%s", "filters": "%s", "query_words": "%s", '
                                     '"members": [{"value": "%s"}, {"value": "%s"}]''}'
                                     % (group_key, new_name, filters, query_words, existing_contact_2, new_contact),
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Contact group details updated. Group members will be updated shortly.')
        count = ContactGroupMember.objects.filter(group=contact_group).count()
        self.assertEquals(count, 3)

        #update exception
        fake_update_contact.side_effect = None
        g_list = list()
        g_list.append(group_key)
        fake_get_contact.return_value = {'key': 'abcde', 'groups': g_list}
        fake_get_contact.side_effect = None
        resp = self.client.post(reverse('group.update'),
                                data='{"group_key": "%s", "name": "%s", "filters": "%s", "query_words": "%s", '
                                     '"members": [{"value": "%s"}, {"value": "%s"}]''}'
                                     % (group_key, new_name, filters, query_words, existing_contact_2, new_contact),
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Contact group details updated. Group members will be updated shortly.')
        count = ContactGroupMember.objects.filter(group=contact_group).count()
        self.assertEquals(count, 2)

    def test_get_surveys(self):
        self.create_survey_result(self.survey, self.contact, {"age": 21})

        resp = self.client.get("/get_surveys/")
        self.assertContains(resp, "0928309402384908203423")


        resp = self.client.post(
            "/get_surveys/",
            content_type='application/json',
            data=json.dumps(
                {
                    "name": "Test",
                    "from": "%s/01/01" % datetime.now().year,
                    "to": "%s/12/31" % datetime.now().year
                }
            )
        )

        self.assertContains(resp, "0928309402384908203423")

    def test_get_unique_keys(self):
        resp = self.client.get("/get_unique_keys/")
        # TODO: Complete Test

    def test_get_answer_values(self):
        user = User.objects.create_user("admin", "admin@admin.com", "admin")
        self.create_survey_result(self.survey, self.contact, {"age": 21, "gender": "male"})
        contact_2 = self.create_contact('+27711234567', '789456123')
        self.create_survey_result(self.survey, contact_2, {"age": 25, "gender": "female", "married": "yes"})

        self.client.post(reverse('login'),
                         {
                             'username': "admin",
                             'password': "admin"
                         },
                         follow=True)

        # get call
        resp = self.client.get(reverse('get_answer_values'))
        self.assertContains(resp, 'Bad Request!', status_code=400)

        # post no data
        resp = self.client.post(reverse('get_answer_values'),
                                data={},
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        #no field
        resp = self.client.post(reverse('get_answer_values'),
                                data='{field: ""}',
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, 'Bad Request!', status_code=400)

        #valid
        resp = self.client.post(reverse('get_answer_values'),
                                data='{"field": "survey"}',
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, self.survey.name)

        resp = self.client.post(reverse('get_answer_values'),
                                data='{"field": "series"}',
                                content_type="application/json",
                                follow=True)
        self.assertContains(resp, self.survey.series)


class ModelTests(TestCase):
    def test_incoming_survey_length_limit(self):
        j = {
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

    def test_setting_lookup(self):
        Setting.objects.create(name="Test", value="test123")

        self.assertIsNone(Setting.get_setting(None))
        self.assertIsNone(Setting.get_setting("tset"))
        self.assertEquals(Setting.get_setting("Test"), "test123")


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
        result, error = process_line(survey_index, survey_key_index, contact_index, contact_key_index, date_index,
                                     header_map, headers, parts)

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
        result, error = process_line(survey_index, survey_key_index, contact_index, contact_key_index, date_index,
                                     header_map, headers, parts)

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
        header_map, survey_index, survey_key_index, contact_index, contact_key_index, date_index = \
            process_header(headers)
        parts = split_line(data_line)
        result, error = process_line(survey_index, survey_key_index, contact_index, contact_key_index, date_index,
                                     header_map, headers, parts)

        self.assertEquals(result, 0)
        self.assertEquals(error, "list index out of range")

        # test not all required fields are present, ie. no answers
        header_line = "survey, survey_key, msisdn, key, timestamp"
        data_line = "Test Survey, 029830492039, 27801231234, 093450934, 2015-03-27T12:08:55.032231"
        headers = split_line(header_line)
        header_map, survey_index, survey_key_index, contact_index, contact_key_index, date_index = \
            process_header(headers)
        parts = split_line(data_line)
        result, error = process_line(survey_index, survey_key_index, contact_index, contact_key_index, date_index,
                                     header_map, headers, parts)

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

        # test empty file
        fout = open(filename, "w")
        fout.close()

        errors, num_rows = process_file(filename)

        self.assertEquals(len(errors), 0)
        self.assertEquals(num_rows, 0)

        os.remove(filename)

        # test non existing file
        errors, num_rows = process_file("/temp/temp/tmp/temp/temp/temp.xtxtemp")

        self.assertEquals(len(errors), 1)
        self.assertEquals(num_rows, 0)

        # test blank lines
        fout = open(filename, "w")
        fout.write("\n\n\n\n")
        fout.close()

        errors, num_rows = process_file(filename)

        self.assertEquals(len(errors), 3)
        self.assertEquals(num_rows, 4)

        os.remove(filename)

        # test file handle processing
        filename = "/tmp/tmp_tmp_tmp_tmp.ttt.xxt"
        fout = open(filename, "w")
        fout.write("survey, survey_key, msisdn, key, timestamp, age, color\n")
        fout.write("Test Survey, 029830492039, 27801231200, 093450934, 2015-03-27T12:08:55.032231, 20, ted\n")
        fout.close()

        fin = open(filename, "r")

        errors, num_rows = process_file(filename=filename, f=fin)

        fin.close()

        self.assertEquals(len(errors), 0)
        self.assertEquals(num_rows, 2)

        survey = Survey.objects.get(name__exact="Test Survey")
        contact = Contact.objects.get(msisdn__exact="27801231200")
        sr = SurveyResult.objects.get(survey=survey, contact=contact)

        self.assertEquals(sr.answer["age"], "20")
        self.assertEquals(sr.answer["color"], "ted")

        os.remove(filename)


class AdminTests(TestCase):

    def admin_page_test_helper(self, c, page):
        resp = c.get(page)
        self.assertEquals(resp.status_code, 200)

    def test_basic_empty_admin(self):
        User.objects.create_user("admin", "admin@admin.com", "admin")
        c = Client()
        c.login(username="admin", password="admin")

        self.admin_page_test_helper(c, "/admin/core/contactgroupmember/")
        self.admin_page_test_helper(c, "/admin/core/contactgroup/")
        self.admin_page_test_helper(c, "/admin/core/contact/")
        self.admin_page_test_helper(c, "/admin/core/exporttypemapping/")
        self.admin_page_test_helper(c, "/admin/core/incomingsurvey/")
        self.admin_page_test_helper(c, "/admin/core/rawsurveyresult/")
        self.admin_page_test_helper(c, "/admin/core/surveyresult/")
        self.admin_page_test_helper(c, "/admin/core/surveyresult/")
        self.admin_page_test_helper(c, "/admin/core/setting/")
        self.admin_page_test_helper(c, "/admin/survey_csv_import/")


class LandingPageStatsTests(TestCase):

    def create_survey(self, survey_id="0928309402384908203423", name="Test"):
        return Survey.objects.create(
            name=name,
            survey_id=survey_id
        )

    def create_contact(self, msisdn="123456789", vkey="234598274987l", **kwargs):
        return Contact.objects.create(
            msisdn=msisdn,
            vkey=vkey,
            **kwargs
        )

    def create_survey_result(self, survey, contact, answers):
        return SurveyResult.objects.create(
            survey=survey,
            contact=contact,
            answer=answers
        )

    def test_landing_page_stats(self):
        User.objects.create_user("admin", "admin@admin.com", "admin")
        c = Client()
        c.login(username="admin", password="admin")

        gender_list = ("male", "female")
        race_list = ("white", "black", "coloured", "indian")
        age_list = range(14, 80)
        yes_no_list = ("yes", "no")

        survey_result_list = list()
        contacts_list = list()

        survey = self.create_survey(survey_id="0928309402384908203499", name="Landing Testing")
        for i in range(0, 5):
            contact = self.create_contact(msisdn='071234567%d' % i, vkey='11223344556%dl' % i)
            contacts_list.append(contact)
            answers = dict()
            answers['gender'] = random.choice(gender_list)
            answers['race'] = random.choice(race_list)
            answers['age'] = random.choice(age_list)
            answers['own_cellphone'] = random.choice(yes_no_list)
            survey_result_list.append(self.create_survey_result(survey=survey, contact=contact,
                                                                answers=answers))

        resp = c.get("/get_stats/")
        json_acceptable_string = resp.content.replace("'", "\"")
        json_resp = json.loads(json_acceptable_string)

        self.assertContains(resp, "total_registered_users")
        self.assertEquals(json_resp['total_registered_users'], 5)
        self.assertContains(resp, "new_registered_users_last_month")
        self.assertEquals(json_resp['new_registered_users_last_month'], 0)
        self.assertContains(resp, "new_registered_users_this_month")
        self.assertEquals(json_resp['new_registered_users_this_month'], 5)
        self.assertContains(resp, "new_registered_users_this_week")
        self.assertEquals(json_resp['new_registered_users_this_week'], 5)
        self.assertContains(resp, "new_registered_users_this_quarter")
        self.assertContains(resp, "total_results")
        self.assertContains(resp, "total_results_last_month")
        self.assertEquals(json_resp['total_results_last_month'], 0)
        self.assertContains(resp, "total_results_this_month")
        self.assertEquals(json_resp['total_results_this_month'], 5)
        self.assertContains(resp, "total_results_this_week")
        self.assertEquals(json_resp['total_results_this_week'], 5)
        self.assertContains(resp, "total_results_this_quarter")
        self.assertContains(resp, "total_surveys")
        self.assertContains(resp, "total_contact_groups")
        self.assertContains(resp, "active_users_this_month")
        self.assertContains(resp, "active_users_this_week")
        self.assertContains(resp, "active_users_this_quarter")
        self.assertContains(resp, "percent_active_this_month")
        self.assertContains(resp, "percent_active_this_week")
        self.assertContains(resp, "percent_active_this_quarter")
        self.assertContains(resp, "drop_this_month")
        self.assertContains(resp, "drop_last_month")

        resp = c.get("/get_graph_data/")
        self.assertContains(resp, 'sms_time_data')
        self.assertContains(resp, 'sms_day_data')
        self.assertContains(resp, 'heading', 2)
        self.assertContains(resp, 'dataset', 2)


class BimeTableTests(TestCase):

    def setUp(self):
        self.j = {
            'user': {
                'answers': {'age': '14'}
            },
            'contact': {
                'extra': {
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

    def test_table_creation(self):

        # create some data
        self.client.post('/save_data/', content_type='application/json', data=json.dumps(self.j))

        construct_summary_table_sql()

        cursor = connection.cursor()
        cursor.execute('select count(1) from gems_reporting.dashboard_survey_results')
        row = cursor.fetchone()

        self.assertEquals(row[0], 1)

        cursor.execute('select age from gems_reporting.dashboard_survey_results')
        row = cursor.fetchone()

        self.assertEquals(row[0], '14')

    def test_table_with_actual_names(self):

        # create some data
        real_data_1 = "{\"user\":{\"answers\":{\"baselineamhnov15\":\"yes\"}},\"contact\":{\"extra\":{\"ep11lemlem-early-marriageeng-1\":\"yes-i-know-someone-who-did\",\"registration-screenlanguage-2\":\"english\",\"registration-screenlanguage-1\":\"\",\"ep6q2mlfemaleeng-1\":\"yes\",\"ep6q2mlfemaleeng\":\"yes\",\"ep6q1gendermleng-1\":\"female\",\"ep6q1gendermleng\":\"female\",\"registration-screenlanguage\":\"english\",\"ep11lemlem-early-marriageeng\":\"yes-i-know-someone-who-did\",\"registration-screenwelcome-page\":\"1\",\"registration-screenwelcome-page-1\":\"1\",\"registration-screenwelcome-page-2\":\"1\",\"baselineamhnov15\":\"yes\",\"baselineamhnov15-1\":\"yes\"},\"groups\":[\"d3eee2c60155485f85d6d026be23dab9\",\"ce1caddf184a452989afdc1f986b57b7\",\"4f9d380135c7491c8471a03a030bc1dc\",\"cd68b1d9a9d74f26943604cdebd5f2c2\",\"3f71aa3cedd1483da837adb366858de2\",\"75e137230248494e8d9bedce48826560\",\"eb595c452e3b4ffe8258b54df9454676\",\"3ee0c069e05b43638b5b09dfdba67410\",\"3e7d667935ad4f11989e577f7afc40e7\",\"1c85ad36dc5c47bfaaabafd0ba5689ba\",\"3ee5089330d0438a9a1d17e3b779cc65\",\"3430cdc770b041608ea1446eada4e9d7\"],\"subscription\":{},\"key\":\"043943a660114f83837821bc61c6190c\",\"twitter_handle\":null,\"user_account\":\"1249b7548d464198b9b10cbb0c3b6415\",\"bbm_pin\":null,\"mxit_id\":null,\"wechat_id\":null,\"email_address\":null,\"facebook_id\":null,\"msisdn\":\"+251924978096\",\"$VERSION\":2,\"gtalk_id\":null,\"name\":null,\"dob\":null,\"created_at\":\"2015-04-20 18:23:56.714918\",\"surname\":null},\"conversation_key\":\"75d0d7d6859347198f4286b2134a6506\"}"
        real_data_2 = "{\"user\":{\"answers\":{\"s6baselinephoamnov15\":\"yes\"}},\"contact\":{\"extra\":{\"ep7agedemographicphoam-1\":\"24\",\"ep12episode-resonance-1phoam-1\":\"very-realistic\",\"ep12episode-resonance-1phoam-2\":\"early-marriage\",\"ep7marriage-viewphoam\":\"yes-completely\",\"ep13episode-inspiredphoam\":\"i-didnt-listen\",\"ep13episode-inspiredphoam-1\":\"i-didnt-listen\",\"agephoam\":\"2\",\"locationphoam\":\"ደብረብረሀን\",\"welcome-and-registration-request\":\"T¡C\",\"question-1-group-d\":\"hulunem\",\"genderphoam\":\"1\",\"question-1-group-d-3\":\"awo\",\"question-1-group-d-3-1\":\"awo\",\"question-1-group-d-1\":\"hulunem\",\"registration\":\"አማርኛ ነዉ\",\"question-1-group-d-2\":\"bekefil-\",\"question-1-group-d-2-1\":\"bekefil-\",\"ep12episode-resonance-1phoam\":\"early-marriage\",\"language\":\"2\",\"ep7agedemographicphoam\":\"24\",\"ep7marriage-viewphoam-1\":\"yes-completely\",\"s6baselinephoamnov15\":\"yes\",\"s6baselinephoamnov15-1\":\"yes\"},\"groups\":[\"5cb9d0195c824aaab4f0983e16fa2172\",\"fffc93e29815442397901e57ef15b311\",\"5f60dfb5c01e4ce1a887e9981e6d47f5\",\"8af6f184df7640899f2849dc5d0aa59c\",\"4f9d380135c7491c8471a03a030bc1dc\",\"cd68b1d9a9d74f26943604cdebd5f2c2\",\"41a0ee4171714538b51a5ee6ff62a8d1\",\"4be1dd04eacc4789910645b8404c19ec\",\"3e7d667935ad4f11989e577f7afc40e7\",\"0a0475ccad194fc8b99425cfe059a328\",\"5bee065a644b4831a6aeea16afb06985\",\"880941dd49b248388226620e4632e913\",\"1d992cd6918c4a5580cbb57b6ef521af\"],\"subscription\":{},\"key\":\"c19d78a9359a4b5b8a7ed2bef3ced0de\",\"twitter_handle\":null,\"user_account\":\"1249b7548d464198b9b10cbb0c3b6415\",\"bbm_pin\":null,\"mxit_id\":null,\"surname\":null,\"wechat_id\":null,\"email_address\":null,\"facebook_id\":null,\"msisdn\":\"+251918255085\",\"gtalk_id\":null,\"name\":null,\"dob\":null,\"created_at\":\"2014-05-30 14:11:50.843054\",\"$VERSION\":2},\"conversation_key\":\"0ab996a154e24918acc8556e6ce44661\"}"
        real_data_3 = "{\"user\":{\"answers\":{\"s6brandquizwk3amh\":\"6\"}},\"contact\":{\"extra\":{\"ep11lemlem-early-marriageamh\":\"yes-i-have\",\"registration-screenlanguage-1\":\"\",\"ep9describe-episodeamh\":\"other\",\"ep9describe-episodeamh-1\":\"other\",\"registration-screenlanguage\":\"\",\"ep11lemlem-early-marriageamh-1\":\"yes-i-have\",\"registration-screenwelcome-page\":\"1\",\"registration-screenwelcome-page-1\":\"1\",\"s6brandquizwk3amh\":\"6\",\"s6brandquizwk3amh-1\":\"6\"},\"groups\":[\"d3eee2c60155485f85d6d026be23dab9\",\"3ee0c069e05b43638b5b09dfdba67410\",\"4c6a42e89b99448fad256a0aaf861b9f\",\"1c85ad36dc5c47bfaaabafd0ba5689ba\",\"3ee5089330d0438a9a1d17e3b779cc65\"],\"subscription\":{},\"key\":\"72641f0fcf1b4e429f66f83c33dd67b0\",\"twitter_handle\":null,\"user_account\":\"1249b7548d464198b9b10cbb0c3b6415\",\"bbm_pin\":null,\"mxit_id\":null,\"surname\":null,\"wechat_id\":null,\"email_address\":\"+251912232001\",\"facebook_id\":null,\"msisdn\":\"+251912232001\",\"$VERSION\":2,\"gtalk_id\":null,\"name\":null,\"dob\":null,\"created_at\":\"2015-06-07 20:30:57.701668\"},\"conversation_key\":\"aaab7a3d25614a32a706f3e118977e40\"}"

        self.client.post('/save_data/', content_type='application/json', data=json.dumps(real_data_1))
        self.client.post('/save_data/', content_type='application/json', data=json.dumps(real_data_2))
        self.client.post('/save_data/', content_type='application/json', data=json.dumps(real_data_3))

        construct_summary_table_sql()
       
        cursor = connection.cursor()
        cursor.execute('select count(1) from gems_reporting.dashboard_survey_results')
        row = cursor.fetchone()

        self.assertEquals(row[0], 3)

        cursor.execute('select baselineamhnov15, s6baselinephoamnov15, s6brandquizwk3amh from gems_reporting.dashboard_survey_results')
        row = cursor.fetchone()

        self.assertEquals(row[0], 'yes')
        self.assertEquals(row[1], None)
        self.assertEquals(row[2], None)

        row = cursor.fetchone()

        self.assertEquals(row[0], None)
        self.assertEquals(row[1], 'yes')
        self.assertEquals(row[2], None)

        row = cursor.fetchone()

        self.assertEquals(row[0], None)
        self.assertEquals(row[1], None)
        self.assertEquals(row[2], '6')
