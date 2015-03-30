from django.db.models import Q
from django.views.generic.base import TemplateView
from models import *
import json


class CreateContactGroupsView(TemplateView):

    template_name = "createcontactgroup.html"

    def get_context_data(self, **kwargs):
        context = super(CreateContactGroupsView, self)\
            .get_context_data(**kwargs)

        contactgroups = ContactGroup.objects.all()
        context['contactgroups'] = contactgroups

        return context


class ContactGroupsView(TemplateView):

    template_name = "contact-groups.html"

    def get_context_data(self, **kwargs):
        context = super(ContactGroupsView, self).get_context_data(**kwargs)

        contactgroups = ContactGroup.objects.all()
        context['contactgroups'] = contactgroups

        return context


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

            # These are the normal fields
            if operator == 'eq' or operator == 'ex':
                kwargs = {
                    '{0}__iexact'.format(field.name): value
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
            if operator == 'eq' or operator == 'ex':
                self.q = Q(answer__exact={field.name: value})
            elif operator == 'gt':
                self.q = Q(answer__gt={field.name: value})
            elif operator == 'gte':
                self.q = Q(answer__gte={field.name: value})
            elif operator == 'lt':
                self.q = Q(answer__lt={field.name: value})
            elif operator == 'lte':
                self.q = Q(answer__lte={field.name: value})
            elif operator == 'co':
                self.q = Q(answer__icontains={field.name: value})
            elif operator == 'neq':
                self.q = ~Q(answer__exact={field.name: value})
            elif operator == 'nco':
                self.q = ~Q(answer__icontains={field.name: value})

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