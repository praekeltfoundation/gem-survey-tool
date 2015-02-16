from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required
from views import user_login, ContactGroupsView, CreateContactGroupsView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', login_required(TemplateView.as_view(template_name='base.html'))),

    url(r'^t/$', (TemplateView.as_view(template_name='t.html'))),

    url(r'^contact-groups/$', login_required(ContactGroupsView.as_view(),
        name='contactgroups')),

    url(r'^contact-groups/create-contact-group/$', login_required(CreateContactGroupsView.as_view(),
        name='createcontactgroup')),

    url(r'^service-dashboard/$', login_required((TemplateView.as_view(template_name='servicedashboard.html')),name='servicedashboard')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^login/$', user_login, name='login'),
)