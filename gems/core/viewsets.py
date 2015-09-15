from gems.core.serializers import *
from gems.core.models import SurveyResult, Contact, Survey, ContactGroup, ContactGroupMember
from rest_framework import viewsets, pagination
from rest_framework.views import Response


class SmallResultSetPagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100000


class SurveyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    pagination_class = SmallResultSetPagination


class SurveyResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SurveyResult.objects.all().prefetch_related("survey", "contact")
    serializer_class = SurveyResultSerializer
    pagination_class = SmallResultSetPagination


class SurveyResultRawViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SurveyResult.objects.all().prefetch_related("survey", "contact")
    serializer_class = SurveyResultSerializer


class ContactViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    pagination_class = SmallResultSetPagination


class ContactGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContactGroup.objects.all()
    serializer_class = ContactGroupSerializer
    pagination_class = SmallResultSetPagination


class ContactGroupMemberViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContactGroupMember.objects.all()
    serializer_class = ContactGroupMemberSerializer
    pagination_class = SmallResultSetPagination