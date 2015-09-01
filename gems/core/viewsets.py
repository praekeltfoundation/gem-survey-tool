from gems.core.serializers import *
from gems.core.models import SurveyResult, Contact, Survey, ContactGroup, ContactGroupMember
from rest_framework import viewsets, pagination


class SmallResultSetPagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    pagination_class = SmallResultSetPagination


class SurveyResultViewSet(viewsets.ModelViewSet):
    queryset = SurveyResult.objects.all()
    serializer_class = SurveyResultSerializer
    pagination_class = SmallResultSetPagination


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    pagination_class = SmallResultSetPagination


class ContactGroupViewSet(viewsets.ModelViewSet):
    queryset = ContactGroup.objects.all()
    serializer_class = ContactGroupSerializer
    pagination_class = SmallResultSetPagination


class ContactGroupMemberViewSet(viewsets.ModelViewSet):
    queryset = ContactGroupMember.objects.all()
    serializer_class = ContactGroupMemberSerializer
    pagination_class = SmallResultSetPagination