from django import VERSION
from django_hstore.hstore import HStoreManager
from django_hstore.query import HStoreQuerySet, HStoreWhereNode
from django.db.models.sql.query import Query
from django.db.models.sql.datastructures import EmptyResultSet
from django.db.models.sql.where import EmptyShortCircuit
from django.utils import six
from django_hstore.utils import get_cast_for_param


class GemsHStoreManager(HStoreManager):
    def get_queryset(self):
        return GemsHStoreQuerySet(self.model, using=self._db)


class GemsHStoreQuerySet(HStoreQuerySet):
    def __init__(self, model=None, query=None, using=None, *args, **kwargs):
        query = query or GemsHStoreQuery(model)
        super(GemsHStoreQuerySet, self).__init__(model=model, query=query, using=using, *args, **kwargs)


class GemsHStoreQuery(Query):
    def __init__(self, model):
        super(GemsHStoreQuery, self).__init__(model, GemsHStoreWhereNode)


class GemsHStoreWhereNode(HStoreWhereNode):

    # FIXME: this method shuld be more clear.
    def make_atom(self, child, qn, connection):
        lvalue, lookup_type, value_annot, param = child
        kwargs = {'connection': connection} if VERSION[:2] >= (1, 3) else {}

        if lvalue and lvalue.field and hasattr(lvalue.field, 'db_type') and lvalue.field.db_type(**kwargs) == 'hstore':
            try:
                lvalue, params = lvalue.process(lookup_type, param, connection)
            except EmptyShortCircuit:
                raise EmptyResultSet()
            field = self.sql_for_columns(lvalue, qn, connection)

            if lookup_type == 'exact':
                if isinstance(param, dict):
                    return ('{0} = %s'.format(field), [param])
                raise ValueError('invalid value')
            elif lookup_type in ('gt', 'gte', 'lt', 'lte'):
                if isinstance(param, dict):
                    sign = (lookup_type[0] == 'g' and '>%s' or '<%s') % (lookup_type[-1] == 'e' and '=' or '')
                    param_keys = list(param.keys())
                    conditions = []
                    for key in param_keys:
                        cast = get_cast_for_param(value_annot, key)
                        conditions.append('(%s->\'%s\')%s %s %%s' % (field, key, cast, sign))
                    return (" AND ".join(conditions), param.values())
                raise ValueError('invalid value')
            elif lookup_type == 'contains':
                if isinstance(param, dict):
                    values = list(param.values())
                    keys = list(param.keys())
                    if len(values) == 1 and isinstance(values[0], (list, tuple)):
                        # Can't cast here because the list could contain multiple types
                        return ('lower(%s->\'%s\') = ANY(%%s)' % (field, keys[0]), [[str(x) for x in values[0]]])
                    elif len(keys) == 1 and len(values) == 1:
                        # Retrieve key and compare to param instead of using '@>' in order to cast hstore value
                        cast = get_cast_for_param(value_annot, keys[0])
                        return ('lower((%s->\'%s\')%s) = lower(%%s)' % (field, keys[0], cast), [values[0]])
                    return ('%s @> %%s' % field, [param])
                elif isinstance(param, (list, tuple)):
                    if len(param) == 0:
                        raise ValueError('invalid value')
                    if len(param) < 2:
                        return ('%s ? %%s' % field, [param[0]])
                    if param:
                        return ('%s ?& %%s' % field, [param])
                    raise ValueError('invalid value')
                elif isinstance(param, six.string_types):
                    # if looking for a string perform the normal text lookup
                    # that is: look for occurence of string in all the keys
                    pass
                elif hasattr(child[0].field, 'serializer'):
                    try:
                        child[0].field._serialize_value(param)
                        pass
                    except Exception:
                        raise ValueError('invalid value')
                else:
                    raise ValueError('invalid value')
            elif lookup_type == 'icontains':
                if isinstance(param, dict):
                    values = list(param.values())
                    keys = list(param.keys())
                    if len(values) == 1 and isinstance(values[0], (list, tuple)):
                        # Can't cast here because the list could contain multiple types
                        return ('lower(%s->\'%s\') = ANY(%%s)' % (field, keys[0]), [[str(x) for x in values[0]]])
                    elif len(keys) == 1 and len(values) == 1:
                        # Retrieve key and compare to param instead of using '@>' in order to cast hstore value
                        cast = get_cast_for_param(value_annot, keys[0])
                        return ('lower((%s->\'%s\')%s) like lower(%%s)' % (field, keys[0], cast), [str(values[0])])
                    return ('%s @> %%s' % field, [param])
                elif isinstance(param, (list, tuple)):
                    if len(param) == 0:
                        raise ValueError('invalid value')
                    if len(param) < 2:
                        return ('%s ? %%s' % field, [param[0]])
                    if param:
                        return ('%s ?& %%s' % field, [param])
                    raise ValueError('invalid value')
                elif isinstance(param, six.string_types):
                    # if looking for a string perform the normal text lookup
                    # that is: look for occurence of string in all the keys
                    pass
                elif hasattr(child[0].field, 'serializer'):
                    try:
                        child[0].field._serialize_value(param)
                        pass
                    except Exception:
                        raise ValueError('invalid value')
                else:
                    raise ValueError('invalid value')
            elif lookup_type == 'isnull':
                if isinstance(param, dict):
                    param_keys = list(param.keys())
                    conditions = []
                    for key in param_keys:
                        op = 'IS NULL' if value_annot[key] else 'IS NOT NULL'
                        conditions.append('(%s->\'%s\') %s' % (field, key, op))
                    return (" AND ".join(conditions), [])
                # do not perform any special format
                return super(GemsHStoreWhereNode, self).make_atom(child, qn, connection)
            else:
                raise TypeError('invalid lookup type')
        return super(GemsHStoreWhereNode, self).make_atom(child, qn, connection)