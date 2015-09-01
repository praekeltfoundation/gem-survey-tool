from django.db import models
from django.contrib.auth.models import User
from django_hstore import hstore
from hstore_helper import GemsHStoreManager


class HStoreModel(models.Model):
    objects = GemsHStoreManager()

    class Meta:
        abstract = True


class Survey(models.Model):
    survey_id = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    created_on = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.name

    def natural_key(self):
        return (self.name)


class Contact(models.Model):
    msisdn = models.CharField(max_length=15, primary_key=True)
    vkey = models.CharField(max_length=32, blank=True, default='')

    def __unicode__(self):
        return self.msisdn


class SurveyResultBase(HStoreModel):
    survey = models.ForeignKey(Survey)
    contact = models.ForeignKey(Contact)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    answer = hstore.DictionaryField()
    sent = models.BooleanField(default=False)

    class Meta:
        abstract = True


class SurveyResult(SurveyResultBase):
    pass


class RawSurveyResult(SurveyResultBase):
    pass


class IncomingSurvey(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    raw_message = models.CharField(max_length=2000)


class ContactGroup(HStoreModel):
    group_id = models.CharField(max_length=5)
    group_key = models.CharField(max_length=32)
    name = models.CharField(max_length=50)
    created_by = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    filters = models.CharField(max_length=8000)
    query_words = models.CharField(max_length=8000)

    def __unicode__(self):
        return u'%s' % (self.name)


class ContactGroupMember(models.Model):
    group = models.ForeignKey(ContactGroup)
    contact = models.ForeignKey(Contact)


class ExportTypeMapping(models.Model):
    casting_choices = (
        (1, 'Cast to Integer'),
        (2, 'Cast to Double')
    )
    field = models.CharField(max_length=50, blank=False, null=False)
    cast = models.IntegerField(choices=casting_choices, blank=False, null=False)