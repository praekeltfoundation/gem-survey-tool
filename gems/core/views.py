from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core import serializers
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.generic import View
from django.shortcuts import render
from go_http.contacts import ContactsApiClient
from forms import SurveyImportForm
from viewhelpers import Filter, UIField, UIFieldEncoder, get_surveyresult_hstore_keys
from csv_utils import process_file
from models import Survey, SurveyResult, IncomingSurvey, Contact, ContactGroupMember, ContactGroup, RawSurveyResult, \
    Setting
import json
import djqscsv
import logging
from datetime import datetime, timedelta
import time
import traceback

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
                request.session['error_msg_line'] = '*Your account has been disabled'
                return HttpResponseRedirect('/login/')
        else:
            # Bad login details were provided. So we can't log the user in.
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


@csrf_exempt
def save_data(request):

    if request.method == 'POST':
        msg = 'save_data - POST - Body[ %s ]' % request.body
        logger.info(msg)

        # log the incoming message
        IncomingSurvey.objects.create(
            raw_message=request.body[:2000]
        )

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

                # add the raw survey result
                RawSurveyResult.objects.create(
                    survey=survey,
                    contact=contact,
                    answer=answers
                )

                sr, created = SurveyResult.objects.get_or_create(
                    survey=survey,
                    contact=contact
                )

                for answer in answers:
                    sr.answer[answer] = answers[answer]

                sr.save()

            except Exception:
                content = {'status': 'failed-ex'}
                traceback.print_exc()
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
    else:
        return None

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

    try:
        rs = SurveyResult.objects.filter(q).values('id', 'survey__name', 'contact', 'created_at', 'updated_at',
                                                   'answer', 'survey__series')
    except Exception:
        rs = SurveyResult.objects.none()

    if random is True:
        rs = rs.order_by('?')
    else:
        rs = rs.order_by("id")

    for item in rs:
        item['series'] = item.pop('survey__series')
        item['survey'] = item.pop('survey__name')

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


def get_surveyresult_meta_keys():
    """
    :rtype: List of UIField objects
    :return: Set of keys from the surveyresult
    """
    field_keys = [
        UIField("id", "N"),
        UIField("survey", "N"),
        UIField("contact", "N"),
        UIField("created_at", "N"),
        UIField("series", "N"),
    ]

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


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


def query(request):
    try:
        payload = json.loads(request.body)
    except ValueError:
        print traceback.print_exc()
        return HttpResponse('BAD REQUEST TYPE')

    results = build_query(payload, True)

    return generate_json_response(json.dumps(list(results), default=json_serial))


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
    Function returns a unique set of fields from SurveyResult and the hstore
    Note: SurveyResult fields are not sorted, only the hstore fields are sorted
    :rtype: HttpResponse
    :return: HttpResponse with json payload
    """
    answer_keys = get_surveyresult_hstore_keys()
    field_keys = get_surveyresult_meta_keys()
    keys = field_keys + sorted(answer_keys, key=lambda f: f.name)

    return generate_json_response(serialize_list_to_json(keys, UIFieldEncoder))


#for testing menu.html in home.html
def view_home(request):
    return render(request, 'home.html')


def get_answer_values(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except ValueError:
            return HttpResponseBadRequest("Bad Request!")

        if 'field' in data and data['field'] is not None:
            rs = SurveyResult.objects.values('answer', 'survey__name').distinct()
            s = Survey.objects.values('series').distinct()
            values = list()
            all_fields = list(rs) + list(s)
            if data['field'] == 'survey':
                field = 'survey__name'
            else:
                field = data['field']

            for item in all_fields:
                if field in item:
                    if item[field] not in values:
                        values.append(item[field])

            return generate_json_response(serialize_list_to_json(values, UIFieldEncoder))

    return HttpResponseBadRequest('Bad Request!')


def delete_contactgroup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except ValueError:
            return HttpResponseBadRequest("Bad Request!")

        if 'group_key' in data and data['group_key'] != '':
            group_key = data['group_key']

            try:
                group = ContactGroup.objects.get(group_key=group_key)
                api = ContactsApiClient(settings.VUMI_TOKEN)
                deleted_group = api.delete_group(group_key)
            except (Exception, ContactGroup.DoesNotExist):
                return HttpResponseBadRequest('Bad Request!')

            if deleted_group['key'] == group_key:
                group.delete()
                return HttpResponse('Contact group deleted!')

    return HttpResponseBadRequest('Bad Request!')


def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s function took %0.3f ms' % (f.func_name, (time2-time1)*1000.0)
        return ret
    return wrap


def process_group_member(api, member, group):
    # if for some reason we don't have the vumi key in the db for this contact, fetch the contact from vumi
    if member.vkey is None or member.vkey == '':
        try:
            contact = api.get_contact(msisdn=member.msisdn)
            member.vkey = contact['key']
            member.save()
        except Exception:
            logger.info('Contact: %s not found in vumi' % member)
            return

    try:
        api.update_contact(member.vkey, {u'groups': (group.group_key, )})
    except Exception:
        logger.info('Contact: %s update failed' % member)
        return

    group_member, created = ContactGroupMember.objects.get_or_create(group=group, contact=member)
    group_member.save()


def remove_group_member(api, member, group):
    try:
        contact = api.get_contact(msisdn=member.msisdn)
        if member.vkey is None or member.vkey == '':
            member.vkey = contact['key']
            member.save()
    except Exception:
        logger.info('Contact: %s not found in vumi' % member)
        return
    groups = contact['groups']
    if group.group_key in groups:
        updated_groups = groups.remove(group.group_key)

        if updated_groups is None:
            updated_groups = ''
        try:
            api.update_contact(member.vkey, {u'groups': updated_groups})
        except Exception:
            logger.info('Contact: %s update failed' % member)
            return

    ContactGroupMember.objects.filter(group=group, contact=member).delete()


def create_contactgroup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except ValueError:
            return HttpResponseBadRequest("Bad Request!")

        if 'name' in data and data['name'] is not None and 'filters' in data and 'query_words' in data:
            group_name = data['name']
            group_filters = data['filters']
            group_query_words = data['query_words']

            api = ContactsApiClient(settings.VUMI_TOKEN)
            data_returned = api.create_group({u'name': group_name, })

            if 'key' in data_returned:
                group_key = data_returned['key']
                date_created = datetime.now()

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
                        try:
                            contact = Contact.objects.get(msisdn=member['value'])
                        except Contact.DoesNotExist:
                            logger.info('Contact with msisdn %s does not exist' % member['value'])
                            continue
                        process_group_member(api, contact, contact_group)

                return HttpResponse("Contact group %s successfully created." % group_name)

    return HttpResponseBadRequest("Bad Request!")


def update_contactgroup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except ValueError:
            return HttpResponseBadRequest("Bad Request!")

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
                    try:
                        new_list.append(Contact.objects.get(msisdn=c['value']))
                    except Contact.DoesNotExist:
                        continue

                o = set(old_list)
                add_list = [x for x in new_list if x not in o]

                n = set(new_list)
                remove_list = [x for x in old_list if x not in n]

                if add_list:
                    logger.info('Adding new contacts to group %s: STARTED' % group.name)
                    for member in add_list:
                        logger.info('Adding contact: %s' % member.msisdn)
                        process_group_member(api, member, group)
                    logger.info('Adding new contacts to group %s: COMPLETED' % group.name)

                if remove_list:
                    logger.info('Removing contacts from group %s: START' % group.name)
                    for member in remove_list:
                        logger.info('Removing contact: %s' % member.msisdn)
                        remove_group_member(api, member, group)
                    logger.info('Removing contacts from group %s: COMPLETED' % group.name)

            return HttpResponse("Contact group updated!")

    return HttpResponseBadRequest("Bad Request!")


def get_surveys(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        results = Survey.objects.all()

        if 'name' in data:
            results = results.filter(name__icontains=data['name'])

        if 'from' in data:
            try:
                date_from = datetime.strptime(data['from'], "%Y/%m/%d")
                results = results.filter(created_on__gte=date_from)
            except ValueError:
                return HttpResponse("Invalid date.")

        if 'to' in data:
            try:
                date_to = datetime.strptime(data['to'], "%Y/%m/%d")
                results = results.filter(created_on__lte=date_to)
            except ValueError:
                return HttpResponse("Invalid date.")

        return generate_json_response(
            serializers.serialize(
                'json',
                list(results)))
    elif request.method == 'GET':
        results = Survey.objects.all()
        return generate_json_response(
            serializers.serialize(
                'json',
                list(results)
            )
        )


def survey_csv_import(request):
    errors = None
    done = None
    num_rows = None
    if request.method == "POST":
        form = SurveyImportForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['file']
            done = True
            errors, num_rows = process_file(filename=f.name, f=f)
        else:
            errors = "No file specified"
    else:
        form = SurveyImportForm()

    return render_to_response(
        "survey_csv_import.html",
        {
            "form": form,
            "errors": errors,
            "num_rows": num_rows,
            "done": done
        },
        context_instance=RequestContext(request)
    )


class LandingStatsView(View):

    def get_today(self):
        return datetime.now()

    def get_this_week(self):
        end = self.get_today()
        start = end.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=end.weekday())
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        return [start, end]

    def get_day_in_last_month(self):
        today = self.get_today().replace(day=1) - timedelta(days=1)
        return today

    def get_this_quarter(self):
        quarter_1 = (1, 2, 3)
        quarter_2 = (4, 5, 6)
        quarter_3 = (7, 8, 9)
        # quarter_4 = ("October", "November", "December")

        today = self.get_today()

        if today.month in quarter_1:
            start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = today.replace(month=3, day=31, hour=23, minute=59, second=59, microsecond=999999)
            return [start, end]
        elif today in quarter_2:
            start = today.replace(month=4, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = today.replace(month=6, day=31, hour=23, minute=59, second=59, microsecond=999999)
            return [start, end]
        elif today in quarter_3:
            start = today.replace(month=7, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = today.replace(month=9, day=31, hour=23, minute=59, second=59, microsecond=999999)
            return [start, end]
        else:
            start = today.replace(month=10, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = today.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            return [start, end]

    def get_stats(self):
        today = self.get_today()
        this_week = self.get_this_week()
        this_month = today.month
        this_year = today.year
        day_in_last_month = self.get_day_in_last_month()
        last_month = day_in_last_month.month
        last_month_year = day_in_last_month.year
        this_quarter = self.get_this_quarter()

        #total users
        total_registered_users = Contact.objects.all().count()

        #new users last month
        new_registered_users_last_month = Contact.objects.filter(
            created_on__month=last_month,
            created_on__year=last_month_year
        ).count()

        #new _registered users this month
        new_registered_users_this_month = Contact.objects.filter(
            created_on__month=this_month,
            created_on__year=this_year
        ).count()

        #new _registered users this week
        new_registered_users_this_week = Contact.objects.filter(
            created_on__range=this_week
        ).count()

        #new _registered users this quarter
        new_registered_users_this_quarter = Contact.objects.filter(
            created_on__range=this_quarter
        ).count()

        #unique users
        sent_sms = SurveyResult.objects.all().values_list('contact__msisdn', flat=True)
        registered_list = Contact.objects.all().values_list('msisdn', flat=True)
        all_users_id_list = list(sent_sms) + list(registered_list)
        unique_users = Contact.objects.filter(msisdn__in=all_users_id_list).count()

        #new users this quarter
        new_users_this_quarter = Contact.objects.filter(msisdn__in=all_users_id_list,
                                                        created_on__range=this_quarter).count()

        #new users this month
        new_users_this_month = Contact.objects.filter(msisdn__in=all_users_id_list,
                                                      created_on__month=this_month,
                                                      created_on__year=this_year).count()

        #new users this week
        new_users_this_week = Contact.objects.filter(msisdn__in=all_users_id_list,
                                                     created_on__range=this_week).count()

        #total survey results
        total_results = SurveyResult.objects.all().count()

        #survey results last month
        total_results_last_month = SurveyResult.objects.filter(
            created_at__month=last_month,
            created_at__year=last_month_year
        ).count()

        #survey results this month
        total_results_this_month = SurveyResult.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year
        ).count()

        #survey results this week
        total_results_this_week = SurveyResult.objects.filter(
            created_at__range=this_week
        ).count()

        #survey results this quarter
        total_results_this_quarter = SurveyResult.objects.filter(
            created_at__range=this_quarter
        ).count()

        #total surveys
        total_surveys = Survey.objects.all().count()

        #total contact groups
        total_contact_groups = ContactGroup.objects.all().count()

        #active this month
        sent_this_month = SurveyResult.objects.filter(created_at__month=this_month,
                                                      created_at__year=this_year)\
            .values_list('contact__msisdn', flat=True)
        active_users_list = [x for x in registered_list if x in sent_this_month]
        active_users_this_month = Contact.objects.filter(msisdn__in=active_users_list).count()

        #active this week
        sent_this_week = SurveyResult.objects.filter(created_at__range=this_week)\
            .values_list('contact__msisdn', flat=True)
        active_users_list = [x for x in registered_list if x in sent_this_week]
        active_users_this_week = Contact.objects.filter(msisdn__in=active_users_list).count()

        #active this quarter
        sent_this_quarter = SurveyResult.objects.filter(created_at__range=this_quarter)\
            .values_list('contact__msisdn', flat=True)
        active_users_list = [x for x in registered_list if x in sent_this_quarter]
        active_users_this_quarter = Contact.objects.filter(msisdn__in=active_users_list).count()

        if total_registered_users > 0:
            percent_active_this_month = "%s%%" % round(active_users_this_month * 100.0 / total_registered_users, 1)
            percent_active_this_week = "%s%%" % round(active_users_this_week * 100.0 / total_registered_users, 1)
            percent_active_this_quarter = "%s%%" % round(active_users_this_quarter * 100.0 / total_registered_users, 1)
        else:
            percent_active_this_month = "0%%"
            percent_active_this_week = "0%%"
            percent_active_this_quarter = "0%%"

        #drop off this month
        sent_this_month = SurveyResult.objects.filter(created_at__month=today.month, created_at__year=today.year)\
            .values_list('contact__msisdn', flat=True)
        drop_off_this_month = len([x for x in registered_list if x not in sent_this_month])

        #drop off last month
        reg_bef_this_month = Contact.objects\
            .filter(created_on__lt=today.replace(day=1, hour=0, minute=0, second=0, microsecond=0))\
            .values_list('msisdn', flat=True)
        sent_last_month = SurveyResult.objects.filter(created_at__month=last_month, created_at__year=last_month_year)\
            .values_list('contact__msisdn', flat=True)
        drop_off_last_month = len([x for x in reg_bef_this_month if x not in sent_last_month])

        return {
            "total_registered_users": total_registered_users,
            "new_registered_users_last_month": new_registered_users_last_month,
            "new_registered_users_this_month": new_registered_users_this_month,
            "new_registered_users_this_week": new_registered_users_this_week,
            "new_registered_users_this_quarter": new_registered_users_this_quarter,
            "unique_users": unique_users,
            "new_users_this_quarter": new_users_this_quarter,
            "new_users_this_month": new_users_this_month,
            "new_users_this_week": new_users_this_week,
            "total_results": total_results,
            "total_results_last_month": total_results_last_month,
            "total_results_this_month": total_results_this_month,
            "total_results_this_week": total_results_this_week,
            "total_results_this_quarter": total_results_this_quarter,
            "total_surveys": total_surveys,
            "total_contact_groups": total_contact_groups,
            "active_users_this_month": active_users_this_month,
            "active_users_this_week": active_users_this_week,
            "active_users_this_quarter": active_users_this_quarter,
            "percent_active_this_month": percent_active_this_month,
            "percent_active_this_week": percent_active_this_week,
            "percent_active_this_quarter": percent_active_this_quarter,
            "drop_this_month": drop_off_this_month,
            "drop_last_month": drop_off_last_month
        }

    def get(self, request):

        return generate_json_response(json.dumps(self.get_stats()))


class LandingPage(View):

    def get(self, request):
        url = Setting.get_setting("VUMI_URL")
        usr = Setting.get_setting("VUMI_USR")
        pwd = Setting.get_setting("VUMI_PWD")

        return render(
            request,
            'base.html',
            {
                "url": url,
                "usr": usr,
                "pwd": pwd
            }
        )


def get_sms_day_data():

    line = list()

    for i in range(6, -1, -1):
        date = datetime.now() - timedelta(days=i)
        count = SurveyResult.objects.filter(created_at__day=date.day,
                                            created_at__month=date.month,
                                            created_at__year=date.year).count()
        line.append((-i, count))

    dataset = list()
    dataset.append(line)

    data = dict()
    data['heading'] = 'Number of SMSes received past 7 days'
    data['dataset'] = dataset

    return data


def get_sms_time_data():

    all_surveys = SurveyResult.objects.all().order_by('created_at')

    line = list()

    for _ in range(0, 24):
        line.append((_, all_surveys.filter(created_at__hour=_).aggregate(Count('id'))['id__count']))

    dataset = list()
    dataset.append(line)

    data = dict()
    data['heading'] = 'Time of day SMSes received'
    data['dataset'] = dataset

    return data


def get_graph_data(request):

    if request.method == 'GET':
        data = dict()
        data['sms_day_data'] = get_sms_day_data()
        data['sms_time_data'] = get_sms_time_data()

        return generate_json_response(json.dumps(data))
