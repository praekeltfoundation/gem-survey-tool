from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core import serializers
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from viewhelpers import *
import json
import djqscsv
from django.shortcuts import render
from go_http.contacts import ContactsApiClient
import logging
import datetime
import re
from gems.core.tasks import export_data


logger = logging.getLogger(__name__)


def user_login(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':

        request.session['wrong_password'] = False

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
                request.session['wrong_password'] = True
                request.session['error_msg_line1'] = '*Your account has been disabled'
                request.session['error_msg_line2'] = ''
                return HttpResponseRedirect('/login/')
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            #return HttpResponse("Invalid login details supplied.")
            request.session['wrong_password'] = True
            request.session['error_msg_line'] = '*Username and password combination incorrect'
            return HttpResponseRedirect('/login/')

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('login.html', {}, context)


def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/login')


def process_extra(extra):
    keys = extra.keys()
    rx = re.compile('-\d+')
    answers = {}

    for key in keys:
        new_key = rx.sub('', key)
        if new_key not in answers:
            answers[new_key] = extra[new_key]

    return answers


@csrf_exempt
def save_data(request):

    if request.method == 'POST':
        msg = 'save_data - POST - Body[ %s ]' % request.body
        logger.info(msg)
        data = json.loads(request.body)
        if type(data) is unicode:
            #decode the string again
            data = json.loads(data)
        answers = None
        contact_msisdn = None
        conversation_key = None
        contact_key = ''

        if 'user' in data:
            user = data['user']

            if 'answers' in user:
                answers = user["answers"]

        if 'contact' in data:
            contact = data['contact']

            if 'msisdn' in contact:
                contact_msisdn = contact['msisdn']

            if 'key' in contact:
                contact_key = contact['key']

        if 'conversation_key' in data:
            conversation_key = data['conversation_key']

        # we have data
        if answers and contact_msisdn and conversation_key:
            try:
                # fetch/create the survey
                try:
                    survey = Survey.objects.get(survey_id__exact=conversation_key)
                except Survey.DoesNotExist:
                    survey = Survey(
                        name='New Survey - Please update',
                        survey_id=conversation_key
                    )
                    survey.save()

                # add the contact
                contact, created = Contact.objects.get_or_create(
                    msisdn=contact_msisdn,
                    vkey=contact_key
                )
                contact.save()

                # add the survey result
                survey_result = SurveyResult(
                    survey=survey,
                    contact=contact,
                    answer=answers
                )
                survey_result.save()
            except Exception:
                content = {'status': 'failed-ex'}
                return generate_json_response(json.dumps(content))
            else:
                content = {'status': 'ok'}
                return generate_json_response(json.dumps(content))
        else:
            content = {'status': 'Failed-bad-data'}
            return generate_json_response(json.dumps(content))
    else:
        content = {'status': 'Failed'}
        return generate_json_response(json.dumps(content))


def build_query(payload, random=False):

    limit = None
    filters = []

    if 'limit' in payload:
        limit = payload['limit']

    if 'filters' in payload:
        for filter_json in payload['filters']:
            filters.append(Filter.decode(filter_json))

    q = None

    for lfilter in filters:
        temp_q = None
        for fieldFilter in lfilter.filters:
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
            if lfilter.loperator == 'or':
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


def export_survey(request):
    if request.method == 'GET':
        if 'pk' in request.GET:
            pk = request.GET['pk']
            qs = SurveyResult.objects.filter(survey__survey_id=pk)
            filename = '%s_survey_results.csv' % pk
            return djqscsv.render_to_csv_response(qs, filename=filename)

    return HttpResponse('Bad request method')


def export_survey_results(request):
    if request.method == 'GET':
        if 'rows' in request.GET:
            rows = json.loads(request.GET['rows'])
            qs = SurveyResult.objects.filter(pk__in=rows)
            return djqscsv.render_to_csv_response(qs)

    return HttpResponse('Bad request method')


def get_exclusion_list():
    """
    Function that returns a list of fields to be excluded from the results
    :rtype : Tuple
    :return: a list of fields to be excluded from the results
    """
    return 'answer',


def get_surveyresult_meta_keys():
    """
    :rtype: List of UIField objects
    :return: Set of keys from the surveyresult meta
    """
    excluded_fields = get_exclusion_list()
    field_keys = []
    sorted_fields = sorted(
        SurveyResult._meta.concrete_fields +
        SurveyResult._meta.many_to_many +
        SurveyResult._meta.virtual_fields
    )

    for field in sorted_fields:
        if field.name not in excluded_fields:
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
            use_natural_keys=True,
            fields=(
                'id',
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


#for testing menu.html in home.html
def view_home(request):
    return render(request, 'home.html')


def get_contact_groups(request):
    #return HttpResponse("hello")
    contact_groups = ContactGroup.objects.all()
    data = serializers.serialize("json", contact_groups)
    return HttpResponse(json.dumps(data), content_type="application/json")


def load_contact_groups(request):
    return render(request, 'contact-groups.html')


def delete_contactgroup(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if 'group_id' in data:
            group_id = data['group_id']

            group = ContactGroup.objects.get(group_id=group_id)
            key = group.group_key
            api = ContactsApiClient(settings.VUMI_TOKEN)
            deleted_group = api.delete_group(key)

            if deleted_group['key'] == key:
                ContactGroup.objects.filter(group_id=group_id).delete()
                return HttpResponse('OK')
            else:
                return HttpResponse('FAILED')
        else:
            return HttpResponse('FAILED')


def process_group_member(api, member, group):
    try:
        contact = api.get_contact(msisdn=member)
    except Exception:
        contact = None
        logger.info('Contact: %s not found in vumi' % member)

    if contact:
        contact['groups'].append(group.group_key)
        try:
            api.update_contact(contact['key'], {u'groups': contact['groups']})
        except Exception:
            logger.info('Contact: %s update failed' % member)

    local_contact = Contact.objects.get(msisdn=member)
    group_member, created = ContactGroupMember.objects.get_or_create(group=group, contact=local_contact)
    group_member.save()


def remove_group_member(api, member, group):
    try:
        contact = api.get_contact(msisdn=member)
    except Exception:
        contact = None
        logger.info('Contact: %s not found in vumi' % member)

    if contact:
        if group.group_key in contact['groups']:
            updated_groups = contact['groups'].remove(group.group_key)

            try:
                api.update_contact(contact['key'], {u'groups': updated_groups})
            except Exception:
                logger.info('Contact: %s update failed' % member)

    local_contact = Contact.objects.get(msisdn=member)
    ContactGroupMember.objects.filter(group=group, contact=local_contact).delete()


def create_contactgroup(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if 'name' in data:
            group_name = data['name']

            api = ContactsApiClient(settings.VUMI_TOKEN)
            data_returned = api.create_group({u'name': group_name, })

            #check if the group key has been returned (checks if the group has been created on vumi)
            if 'key' in data_returned:
                group_key = data_returned['key']

                if 'filters' in data:
                    group_filters = data['filters']

                    if 'query_words' in data:
                        group_query_words = data['query_words']

                        date_created = datetime.datetime.now()

                        contact_group = ContactGroup.objects.create(
                            group_key=group_key,
                            name=group_name,
                            created_by=request.user,
                            created_at=date_created,
                            filters=group_filters,
                            query_words=group_query_words
                        )

                        if 'members' in data:
                            members = data['members']

                            for member in members:
                                process_group_member(api, member, contact_group)

                            return HttpResponse("OK")

        return HttpResponse("FAILED")
    else:
        return HttpResponse("FAILED.")


def update_contactgroup(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if 'group_key' in data:
            group_key = data['group_key']
            group = ContactGroup.objects.get(group_key=group_key)
            api = ContactsApiClient(settings.VUMI_TOKEN)

            if 'name' in data:
                group_name = data['name']

                if group_name != group.name:
                    api.update_group(group_key, {u'name': group_name})
                    group.name = group_name
                    group.save(update_fields=['name'])

            if 'filters' in data:
                group.filters = data['filters']
                group.save()

            if 'query_words' in data:
                group.query_words = data['query_words']
                group.save()

            if 'members' in data:
                members = data['members']

                cgm = ContactGroupMember.objects.filter(group=group)
                old_list = []
                for c in cgm:
                    old_list.append(Contact.objects.get(msisdn=c.contact))

                new_list = []
                for c in members:
                    new_list.append(Contact.objects.get(msisdn=c))

                o = set(old_list)
                add_list = [x for x in new_list if x not in o]

                n = set(new_list)
                remove_list = [x for x in old_list if x not in n]

                if add_list:
                    print "Adding:"
                    for member in add_list:
                        print member
                        print type(member) is Contact
                        process_group_member(api, member, group)

                if remove_list:
                    print "Removing:"
                    for member in remove_list:
                        print member
                        print type(member) is Contact
                        remove_group_member(api, member, group)

            return HttpResponse("OK")
        else:
            return HttpResponse("FAILED")
    else:
        return HttpResponse("FAILED")


def get_surveys(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        results = Survey.objects.select_related().all()

        if 'name' in data:
            results = results.filter(name__contains=data['name'])

        if 'from' in data:
            try:
                date_from = datetime.datetime.strptime(data['from'], "%Y/%m/%d")
                results = results.filter(created_on__gte=date_from)
            except ValueError:
                return HttpResponse("Invalid date.")

        if 'to' in data:
            try:
                date_to = datetime.datetime.strptime(data['to'], "%Y/%m/%d")
                results = results.filter(created_on__lte=date_to)
            except ValueError:
                return HttpResponse("Invalid date.")

        return generate_json_response(
            serializers.serialize(
                'json',
                list(results)))
    else:
        return HttpResponse("FAILED")