from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.base import TemplateView
from django.core import serializers
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from models import *
import json
import djqscsv
from django.shortcuts import render

from go_http.contacts import ContactsApiClient

#token for vumi authentication
VUMI_TOKEN = '996CA00F-6184-4734-B28F-0A56FD8367A3'

import logging

logger = logging.getLogger(__name__);

def user_login(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value),
        # no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your GEM account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('login.html', {}, context)


class ContactGroupsView(TemplateView):

    template_name = "contact-groups.html"

    def get_context_data(self, **kwargs):
        context = super(ContactGroupsView, self).get_context_data(**kwargs)

        contactgroups = ContactGroup.objects.all()
        context['contactgroups'] = contactgroups

        return context


class CreateContactGroupsView(TemplateView):

    template_name = "createcontactgroup.html"

    def get_context_data(self, **kwargs):
        context = super(CreateContactGroupsView, self)\
            .get_context_data(**kwargs)

        contactgroups = ContactGroup.objects.all()
        context['contactgroups'] = contactgroups

        return context


@csrf_exempt
def save_data(request):

    if(request.method == 'POST'):
        msg = 'save_data - POST - Body[ %s ]' %(request.body);
        f = open('/tmp/debug.log', 'a')
        f.write('%s\n' % (msg))
        f.close()
        logger.info(msg);
        data=json.loads(request.body)
        if type(data) is unicode:
            #decode the string again
            data=json.loads(data);
        answers = None
        contact_msisdn = None
        conversation_key = None

        if 'user' in data:
            user = data['user']
            if 'answers' in user:
                answers = user["answers"]
        if 'contact' in data:
            contact = data['contact']
            if 'msisdn' in contact:
                contact_msisdn = contact['msisdn']
        if 'conversation_key' in data:
            conversation_key = data['conversation_key']

        # we have data
        if answers and contact_msisdn and conversation_key:
            try:
                # fetch/create the survey
                # fix this
                survey, created = Survey.objects.get_or_create(
                    survey_id=conversation_key,
                    defaults={
                        'survey_id': conversation_key,
                        'name': 'New Survey - Please update name in Admin '
                                'console'
                    })
                survey.save()
                # add the contact
                contact, created = Contact.objects.get_or_create(
                    msisdn=contact_msisdn)
                contact.save()
                # add the survey result
                survey_result = SurveyResult(
                    survey=survey,
                    contact=contact,
                    answer=answers
                )
                survey_result.save()
            except Exception:
                return HttpResponse('FAILED-EX')
            else:
                return HttpResponse('OK')
    else:
            return HttpResponse('FAILED-BAD-DATA')
    else:
        return HttpResponse('FAILED')


class FieldFilter:
    def __init__(self, operator, value, field, loperator=None):
        self.operator = operator
        self.value = value

        if loperator is None:
            self.loperator = 'and'
        else:
            self.loperator = loperator

        self.field = field
        self.q = None

        if field.type == 'N':
            # These are the normal fields
            if operator == 'eq' or operator == 'ex':
                kwargs = {
                    '{0}'.format(field.name): value
                }
                self.q = Q(**kwargs)
            elif operator == 'gt' \
                    or operator == 'gte' \
                    or operator == 'lt' \
                    or operator == 'lte':
                kwargs = {
                    '{0}__{1}'.format(field.name, operator): value
                }
                self.q = Q(**kwargs)
            elif operator == 'co':
                kwargs = {
                    '{0}__contains'.format(field.name): value
                }
                self.q = Q(**kwargs)
            elif operator == 'neq':
                kwargs = {
                    '{0}'.format(field.name): value
                }
                self.q = ~Q(**kwargs)
            elif operator == 'nco':
                kwargs = {
                    '{0}__contains'.format(field.name): value
                }
                self.q = ~Q(**kwargs)
        else:
            # These are the hstore fields
            if operator == 'eq' or operator == 'ex':
                self.q = Q(answer={field.name: value})
            elif operator == 'gt':
                self.q = Q(answer__gt={field.name: value})
            elif operator == 'gte':
                self.q = Q(answer__gte={field.name: value})
            elif operator == 'lt':
                self.q = Q(answer__lt={field.name: value})
            elif operator == 'lte':
                self.q = Q(answer__lte={field.name: value})
            elif operator == 'co':
                self.q = Q(answer__contains={field.name: value})
            elif operator == 'neq':
                self.q = ~Q(answer={field.name: value})
            elif operator == 'nco':
                self.q = ~Q(answer__contains={field.name: value})

    @staticmethod
    def decode(json, field):
        op = json['operator']
        value = json['value']
        lop = None
        if 'loperator' in json:
            lop = json['loperator']

        return FieldFilter(op, value, field, lop)


class Filter:
    def __init__(self, field, filters=[], loperator=None):
        self.field = field
        self.filters = filters

        if loperator is None:
            self.loperator = 'and'
        else:
            self.loperator = loperator

    @staticmethod
    def decode(json):
        field = UIField.decode(json['field'])
        lop = None

        if 'loperator' in json:
            lop = json['loperator']

        local_filters = []
        temp_filters = json['filters']
        for temp_filter in temp_filters:
            local_filters.append(FieldFilter.decode(temp_filter, field))

        return Filter(field, local_filters, lop)


def build_query(payload, random=False):

    limit = None
    filters = []

    if 'limit' in payload:
        limit = payload['limit']

    if 'filters' in payload:
        for filter_json in payload['filters']:
            filters.append(Filter.decode(filter_json))

    q = None

    for filter in filters:
        temp_q = None
        for fieldFilter in filter.filters:
            if temp_q is None:
                temp_q = fieldFilter.q
            else:
                if fieldFilter.loperator == 'or':
                    temp_q = temp_q | fieldFilter.q
                else:
                    temp_q = temp_q & fieldFilter.q

        if q is None:
            q = temp_q
        else:
            if filter.loperator == 'or':
                q = q | temp_q
            else:
                q = q & temp_q

    rs = SurveyResult.objects.filter(q)

    if random is True:
        rs = rs.order_by('?')

    if limit is not None:
        return rs[:limit]
    else:
        return rs


@csrf_exempt
def export(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        qs = build_query(payload)
        return djqscsv.render_to_csv_response(qs)
    else:
        return HttpResponse('Bad request method')


class UIField:
    def __init__(self, name, field_type):
        if type(name) is tuple:
            self.name = name[0]
        else:
        self.name = name
        self.type = field_type

    @staticmethod
    def decode(json):
        return UIField(json['name'], json['type'])


class UIFieldEncoder(json.JSONEncoder):
    def default(self, obj):
        """
        :type obj: UIField
        """
        if isinstance(obj, UIField):
            retVal = {}
            retVal["name"] = obj.name
            retVal["type"] = obj.type
            return retVal
        return json.JSONEncoder.default(self, obj)


def get_exclusion_list():
    """
    Function that returns a list of fields to be excluded from the results
    :rtype : Tuple
    :return: a list of fields to be excluded from the results
    """
    return ('id', 'answer')


def get_surveyresult_meta_keys():
    """
    :rtype: List of UIField objects
    :return: Set of keys from the surveyresult meta
    """
    excluded_fields = get_exclusion_list()
    field_keys = []

    for field in sorted(
            SurveyResult._meta.concrete_fields +
            SurveyResult._meta.many_to_many +
            SurveyResult._meta.virtual_fields):
        if field.name not in  excluded_fields:
            field_keys.append(UIField(field.name, 'N'))

    return field_keys


def serialize_list_to_json(data, encoder):
    """
    Serialize data to a json string
    :param data: List of objects to serialize
    :param encoder: The encoder to use for the type
    :rtype: string
    :return: data serialized as a json string
    """
    return json.dumps(data, cls=encoder)


@csrf_exempt
def query(request):
    """

    :param request:
    :return:
    """
    payload = json.loads(request.body)
    results = build_query(payload, True)

    return generate_json_response(
        serializers.serialize(
            'json',
            list(results),
            fields=(
                'survey',
                'contact',
                'created_at',
                'updated_at',
                'answer')))


def get_surveyresult_hstore_keys():
    """
    :rtype: List of UIField objects
    :return: Unique set of keys from the answer hstore field in the
             surveyresult table
    """
    sql = 'select distinct hKey ' \
          'from (select skeys(answer) as hKey ' \
          'from core_surveyresult) as dt'
    cursor = connection.cursor()
    answer_keys = []

    cursor.execute(sql)

    for answer_key in cursor.fetchall():
        answer_keys.append(UIField(answer_key, 'H'))

    return answer_keys


def generate_json_response(content):
    """
    :param content: JSON content for the response body
    :rtype: HttpResponse
    :return: Returns a JSON response
    """

    response = HttpResponse(content, content_type='application/json')
    response['Content-Length'] = len(content)

    return response


def get_unique_keys(request):
    """
    Function returns a unique set of fields from the meta and the hstore
    :rtype: HttpResponse
    :return: HttpResponse with json payload
    """
    answer_keys = get_surveyresult_hstore_keys()
    field_keys = get_surveyresult_meta_keys()
    keys = sorted(answer_keys + field_keys, key=lambda f: f.name)

    return generate_json_response(serialize_list_to_json(keys, UIFieldEncoder))


# for testing menu.html in home.html
def view_home(request):
    return render(request, 'home.html')

def get_contact_groups(request):
    return HttpResponse("hello")
    #contact_groups = ContactGroup.objects.all()
    #data = serializers.serialize("json", contact_groups)
    #return HttpResponse(json.dump(data), content_type="application/json")

def load_contact_groups(request):
    return render(request, 'contact-groups.html')

def delete_group_contact(request):
    if(request.method == 'POST'):
        data=json.loads(request.body)
        group_id = None

        if data.has_key('group_id'):
             group_id = data['group_id']

        ContactGroup.objects.filter(group_id=group_id).delete()

        key = 'f578cbcb16bc4171a7ccc50d250dca96'
        api = ContactsApiClient(VUMI_TOKEN)
        api.delete_group(key)

        return HttpResponse('OK')
    else:
        return HttpResponse('FAILED')

def create_groupcontact(request):
    if request.method == 'POST':
        data=json.loads(request.body)

        if data.has_key('group_name'):
            group_data = {u'name': data['group_name'],}

        api = ContactsApiClient(VUMI_TOKEN)
        group = api.create_group(group_data)
        return HttpResponse(group[u'key'])
    else:
        return HttpResponse("Failed to create group.")

def update_groupcontact(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if data.has_key('group_key'):
            group_key = {u'key': data['group_key'],}

        if data.has_key('group_name'):
            group_name = {u'name': data['group_name'],}

        api = ContactsApiClient(VUMI_TOKEN)
        api.update_group(group_key, group_name)



def create_contact(request):
    if request.method == 'POST':
        data=json.loads(request._body)

        if data.has_key(''):
            data =  0

        api = ContactsApiClient(VUMI_TOKEN)
        api.create_contact()
        return HttpResponse()
    else:
        return HttpResponse()

def update_contact(request):
    api = ContactsApiClient(VUMI_TOKEN)
    api.update_contact()
    return HttpResponse()

def delete_contact(request):

    api = ContactsApiClient(VUMI_TOKEN)
    api.delete_contact()
    return HttpResponse()