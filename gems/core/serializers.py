from gems.core.models import SurveyResult, Contact, ContactGroup, Survey, ContactGroupMember
from rest_framework import serializers


class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = ('survey_id', 'name', 'created_on')


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('vkey',)


class SurveyResultSerializer(serializers.ModelSerializer):
    survey = SurveySerializer(read_only=True)
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = SurveyResult
        fields = ('survey', 'contact', 'answer', 'created_at')


class ContactGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactGroup
        fields = ('name', 'created_at', 'group_key', 'filters', 'query_words')


class ContactGroupMemberSerializer(serializers.ModelSerializer):
    group = ContactGroupSerializer(read_only=True)
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = ContactGroupMember
        fields = ('group', 'contact')