from django.contrib import admin
from .models import Survey, Contact, SurveyResults


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ContactAdmin(admin.ModelAdmin):
    list_display = ('msisdn',)


class SurveyResultsAdmin(admin.ModelAdmin):
    list_display = ('survey_id','msisdn','answer')



admin.site.register(Survey, SurveyAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(SurveyResults, SurveyResultsAdmin)
