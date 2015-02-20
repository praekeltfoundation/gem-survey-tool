from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required
from views import user_login, ContactGroupsView, CreateContactGroupsView, save_data, export, view_home
from django.contrib import admin
from rest_framework import routers, serializers, viewsets
from gems.core.viewsets import SurveyResultViewSet, ContactViewSet, SurveyViewSet, ContactGroupViewSet, \
    ContactGroupMemberViewSet

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'surveyresult', SurveyResultViewSet)
router.register(r'contact', ContactViewSet)
router.register(r'survey', ContactViewSet)
router.register(r'contactgroup', ContactGroupViewSet)
router.register(r'contactgroupmember', ContactGroupMemberViewSet)

urlpatterns = patterns('',
    url(r'^$', login_required(TemplateView.as_view(template_name='base.html'))),


    url(r'^contact-groups/$', login_required(ContactGroupsView.as_view()),
        name='contactgroups'),

    url(r'^contact-groups/create-contact-group/$', login_required(CreateContactGroupsView.as_view()),
        name='createcontactgroup'),

    url(r'^service-dashboard/$', login_required(TemplateView.as_view(template_name='servicedashboard.html'))),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^login/$', user_login, name='login'),

    url(r'^', include(router.urls)),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^save_data/', save_data, name='saveData'),

    url(r'^export/', export, name='export'),
    url(r'^home/$', view_home, name='home'),
)