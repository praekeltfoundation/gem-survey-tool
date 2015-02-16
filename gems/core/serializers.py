from gems.core.models import SurveyResult, Contact, ContactGroup, Survey, ContactGroupMember
from rest_framework import routers, serializers, viewsets
from django.contrib.auth.models import User

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

class SurveySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Survey
        fields = { 'survey_id', 'name' }

class SurveyResultSerializer(serializers.HyperlinkedModelSerializer):
    survey_id = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='survey_id-detail'
    )

    contact = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='contact-detail'
    )

    class Meta:
        model = SurveyResult
        fields = ( 'survey_id', 'contact', 'answer')


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Contact
        fields = ('msisdn', 'age', 'gender')


class ContactGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContactGroup
        fields = ('group_id', 'name', 'created_at', 'rules')

class ContactGroupMemberSerializer(serializers.HyperlinkedModelSerializer):
    group = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='contactgroup-detail'
    )

    contact = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='contact-detail'
    )

    class Meta:
        model = ContactGroupMember
        fields = ('group', 'contact')