from django.db import models
from django.contrib.auth.models import User
from django_hstore import hstore


class HStoreModel(models.Model):
    objects = hstore.HStoreManager()

    class Meta:
        abstract = True


class Survey(models.Model):
    survey_id = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return  u'%s' % self.name


class Contact(models.Model):
    msisdn = models.CharField(max_length=15, primary_key=True)

    def __unicode__(self):
        return self.msisdn


class SurveyResult(HStoreModel):
    survey = models.ForeignKey(Survey)
    contact = models.ForeignKey(Contact)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    answer = hstore.DictionaryField()


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