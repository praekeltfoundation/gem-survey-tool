from django.db import models
from django_hstore import hstore


class HStoreModel(models.Model):
    objects = hstore.HStoreManager()

    class Meta:
        abstract = True


class Survey(models.Model):
    survey_id = models.CharField(max_length=50)
    name=models.CharField(max_length=200)


class Contact(models.Model):
    msisdn = models.CharField(max_length=12)
    age = models.CharField(max_length=12)
    gender = models.CharField(max_length=12)


class SurveyResults(HStoreModel):
    survey_id = models.ForeignKey(Survey)
    msisdn = models.ForeignKey(Contact)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    answer = hstore.DictionaryField()




