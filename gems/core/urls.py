from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import admin
from rest_framework import routers

from views import survey_csv_import, user_login, user_logout, save_data, export_survey, export_survey_results, \
    query, get_unique_keys, view_home, load_contact_groups, delete_contactgroup, create_contactgroup, \
    update_contactgroup, get_surveys, LandingStatsView
from gems.core.viewsets import SurveyResultViewSet, ContactGroupMemberViewSet, ContactViewSet, SurveyViewSet, \
    ContactGroupViewSet

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'surveyresult', SurveyResultViewSet)
router.register(r'contact', ContactViewSet)
router.register(r'survey', SurveyViewSet)
router.register(r'contactgroup', ContactGroupViewSet)
router.register(r'contactgroupmember', ContactGroupMemberViewSet)

urlpatterns = patterns('',
    url(r'^$', login_required(TemplateView.as_view(template_name='base.html'))),

    url(r"^admin/survey_csv_import/$", survey_csv_import),

    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^login/$', user_login, name='login'),

    url(r'^logout/$', user_logout, name='logout'),

    url(r'^', include(router.urls)),

    url(r'^save_data/', save_data, name='save_data'),

    url(r'^export_survey/', export_survey, name='export_survey'),
    url(r'^export_survey_results/$', export_survey_results, name='export_survey_results'),

    url(r'^query/', query, name='query'),

    url(r'^get_unique_keys/', get_unique_keys, name='get_unique_keys'),
    url(r'^home/$', view_home, name='home'),

    url(r'^contactgroup/$', load_contact_groups),
    url(r'^delete_contactgroup/', delete_contactgroup),
    url(r'^create_contactgroup/', create_contactgroup),
    url(r'^update_contactgroup/', update_contactgroup),
    url(r'^get_surveys/$', get_surveys),

    url(r"^get_stats/$", login_required(LandingStatsView.as_view())),

    url(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", mimetype="text/plain")),
)