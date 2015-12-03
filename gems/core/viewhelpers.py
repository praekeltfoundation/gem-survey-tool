from django.db.models import Q
from django.db import connection
import json


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