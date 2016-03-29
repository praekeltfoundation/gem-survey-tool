from django.db import models
from django.contrib.auth.models import User
from django_hstore import hstore
from hstore_helper import GemsHStoreManager
from datetime import datetime


class HStoreModel(models.Model):
    objects = GemsHStoreManager()

    class Meta:
        abstract = True


class Survey(models.Model):
    survey_id = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    created_on = models.DateField(auto_now_add=True)
    series = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

    def natural_key(self):
        return (self.name, )


class Contact(models.Model):
    msisdn = models.CharField(max_length=15, primary_key=True)
    vkey = models.CharField(max_length=32, blank=True, default='')
    created_on = models.DateField(auto_now_add=True, default=datetime.now(), blank=False)

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
    group_key = models.CharField(max_length=32)
    name = models.CharField(max_length=50)
    created_by = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    filters = models.CharField(max_length=8000)
    query_words = models.CharField(max_length=8000)

    def __unicode__(self):
        return u'%s' % self.name


class ContactGroupMember(models.Model):
    group = models.ForeignKey(ContactGroup)
    contact = models.ForeignKey(Contact)
    synced = models.BooleanField(default=False)


class ExportTypeMapping(models.Model):
    casting_choices = (
        (1, 'Cast to Integer'),
        (2, 'Cast to Double')
    )
    field = models.CharField(max_length=50, blank=False, null=False)
    cast = models.IntegerField(choices=casting_choices, blank=False, null=False)


class Setting(models.Model):
    name = models.CharField(max_length=64)
    value = models.CharField(max_length=1024)

    @staticmethod
    def get_setting(name):
        if name:
            rs = Setting.objects.filter(name=name).first()

            if rs:
                return rs.value

        return None


class SentMessage(models.Model):
    created_at = models.DateField("Date", blank=False, null=False)
    total = models.IntegerField("Number of Sent SMSes", blank=False, null=False)

    class Meta:
        verbose_name = 'Sent Messages'
        verbose_name_plural = 'Sent Messages'


class VumiChannel(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vumi Channels'
        verbose_name_plural = 'Vumi Channels'
