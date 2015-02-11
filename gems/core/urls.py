from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from views import user_login

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='home.html')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^login/$', user_login, name='login'),
)