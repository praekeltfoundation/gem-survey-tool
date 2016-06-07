from django.db.models import Q
from django.db import connection
import json
from gems.core.models import ContactGroupMember, TaskLogger
import logging

logger = logging.getLogger(__name__)


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

            if field.name == 'survey':
                field.name = 'survey__name'

            if field.name == 'series':
                field.name = 'survey__series'

            if field.name == 'contact':
                field.name = 'contact__msisdn'

            # These are the normal fields
            if operator == 'eq':
                kwargs = {
                    '{0}__iexact'.format(field.name): value
                }
                self.q = Q(**kwargs)
            elif operator == 'ex':
                kwargs = {
                    '{0}__exact'.format(field.name): value
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
                    '{0}__icontains'.format(field.name): value
                }
                self.q = Q(**kwargs)
            elif operator == 'neq':
                kwargs = {
                    '{0}'.format(field.name): value
                }
                self.q = ~Q(**kwargs)
            elif operator == 'nco':
                kwargs = {
                    '{0}__icontains'.format(field.name): value
                }
                self.q = ~Q(**kwargs)
        else:
            # These are the hstore fields
            # Special hack!!!
            # * contains is a sql ==
            # * icontains is a sql like
            if operator == 'eq':
                self.q = Q(answer__contains={field.name: value})
            elif operator == 'ex':
                self.q = Q(answer__contains={field.name: value})
            elif operator == 'gt':
                self.q = Q(answer__gt={field.name: value})
            elif operator == 'gte':
                self.q = Q(answer__gte={field.name: value})
            elif operator == 'lt':
                self.q = Q(answer__lt={field.name: value})
            elif operator == 'lte':
                self.q = Q(answer__lte={field.name: value})
            elif operator == 'co':
                self.q = Q(answer__icontains={field.name: "%" + value + "%"})
            elif operator == 'neq':
                self.q = ~Q(answer__contains={field.name: value})
            elif operator == 'nco':
                self.q = ~Q(answer__icontains={field.name: "%" + value + "%"})

    @staticmethod
    def decode(payload, field):
        op = payload['operator']
        value = payload['value']
        lop = None
        if 'loperator' in payload:
            lop = payload['loperator']

        return FieldFilter(op, value, field, lop)


class Filter:
    def __init__(self, field, filters=None, loperator=None):
        self.field = field
        self.filters = filters

        if self.filters is None:
            self.filters = []

        if loperator is None:
            self.loperator = 'and'
        else:
            self.loperator = loperator

    @staticmethod
    def decode(payload):
        field = UIField.decode(payload['field'])
        lop = None

        if 'loperator' in payload:
            lop = payload['loperator']

        local_filters = []
        temp_filters = payload['filters']
        for temp_filter in temp_filters:
            local_filters.append(FieldFilter.decode(temp_filter, field))

        return Filter(field, local_filters, lop)


class UIField:
    def __init__(self, name, field_type):
        if type(name) is tuple:
            self.name = name[0]
        else:
            self.name = name
        self.type = field_type

    @staticmethod
    def decode(payload):
        return UIField(payload['name'], payload['type'])


class UIFieldEncoder(json.JSONEncoder):
    def default(self, obj):
        """
        :type obj: UIField
        """
        if isinstance(obj, UIField):
            retval = {
                'name': obj.name,
                'type': obj.type
            }
            return retval
        else:
            return json.JSONEncoder.default(self, obj)


def get_surveyresult_hstore_keys(ui_field=True):
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
        if ui_field:
            answer_keys.append(UIField(answer_key, 'H'))
        else:
            if type(answer_key) is tuple:
                answer_keys.append(answer_key[0])
            else:
                answer_keys.append(answer_key)

    return answer_keys


def process_group_member(api, member, group):
    # if for some reason we don't have the vumi key in the db for this contact, fetch the contact from vumi
    task_name = 'process_group_member'
    msg = 'Processing member. msisdn: %s' % member.msisdn
    TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
    if member.vkey is None or member.vkey == '':
        try:
            msg = 'Processing member with no vkey %s. Getting the key from Vumi (get_contact)' % member.vkey
            TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
            contact = api.get_contact(msisdn=member.msisdn)
            msg = 'Contact (msisdn: %s) retrieved from Vumi. vkey = %s' % (member.msisdn, contact['key'])
            TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
            member.vkey = contact['key']
            msg = 'Updating contact :: STARTED'
            TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
            member.save()
            msg = 'Updating contact :: COMPLETED'
            TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
        except Exception as e:
            msg = 'Contact: %s not found in vumi. %s' % (member, e)
            TaskLogger.objects.create(task_name=task_name, success=False, message=msg)
            logger.info(msg)
            return

    try:
        msg = 'Getting contact group member. group = %s, contact = %s :: STARTING' % (group.name, member.msisdn)
        TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
        group_member, created = ContactGroupMember.objects.get_or_create(group=group, contact=member)
        msg = 'Getting contact group member. group = %s, contact = %s :: COMPLETED' % (group.name, member.msisdn)
        TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
    except Exception as e:
        msg = 'Failed to add %s contact to %s group. %s' % (member.msisdn, group.name, e)
        TaskLogger.objects.create(task_name=task_name, success=False, message=msg)
        logger.exception(msg)

    try:
        msg = 'Updating contact on Vumi :: STARTED'
        TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
        api.update_contact(member.vkey, {u'groups': (group.group_key, )})
        msg = 'Updating contact on Vumi :: COMPLETED'
        TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
        group_member.synced = True
        msg = 'Updating contact :: STARTED'
        TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
        group_member.save()
        msg = 'Updating contact:: COMPLETED'
        TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
    except Exception as e:
        msg = 'Contact: %s update failed. %s' % (member.msisdn, e)
        TaskLogger.objects.create(task_name=task_name, success=False, message=msg)
        logger.info(msg)


def remove_group_member(api, member, group):
    task_name = 'remove_group_member'
    try:
        msg = 'Getting contact from Vumi. msisdn: %s' % member.msisdn
        TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
        contact = api.get_contact(msisdn=member.msisdn)
        if member.vkey is None or member.vkey == '':
            member.vkey = contact['key']
            msg = 'Updating vkey :: STARTED'
            TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
            member.save()
            msg = 'Updating vkey :: COMPLETED'
            TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
    except Exception as e:
        msg = 'Contact: %s not found in vumi. %s' % (member, e)
        TaskLogger.objects.create(task_name=task_name, success=False, message=msg)
        logger.info(msg)
        return
    groups = contact['groups']
    if group.group_key in groups:
        updated_groups = groups.remove(group.group_key)

        if updated_groups is None:
            updated_groups = ''
        try:
            msg = 'Updating contact groups :: STARTED'
            TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
            api.update_contact(member.vkey, {u'groups': updated_groups})
            msg = 'Updating contact groups :: COMPLETED'
            TaskLogger.objects.create(task_name=task_name, success=True, message=msg)
        except Exception as e:
            msg = 'Contact: %s update failed. %s' % (member, e)
            TaskLogger.objects.create(task_name=task_name, success=False, message=msg)
            logger.info(msg)
            return

    try:
        ContactGroupMember.objects.filter(group=group, contact=member).delete()
    except Exception as e:
        msg = 'Failed to delete %s contact in %s group. %s' % (member.msisdn, group.name, e)
        TaskLogger.objects.create(task_name=task_name, success=False, message=msg)
        logger.exception(msg)