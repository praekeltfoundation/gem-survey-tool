from gems.core.serializers import *
from gems.core.models import SurveyResult, Contact, Survey, ContactGroup, ContactGroupMember
from rest_framework import viewsets


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer

class SurveyResultViewSet(viewsets.ModelViewSet):
    queryset = SurveyResult.objects.all()
    serializer_class = SurveyResultSerializer

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

class ContactGroupViewSet(viewsets.ModelViewSet):
    queryset = ContactGroup.objects.all()
    serializer_class = ContactGroupSerializer

class ContactGroupMemberViewSet(viewsets.ModelViewSet):
    queryset = ContactGroupMember.objects.all()
    serializer_class = ContactGroupMemberSerializer