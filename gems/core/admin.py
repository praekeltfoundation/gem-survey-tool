from django.contrib import admin
from models import Survey, Contact, SurveyResults, ContactGroup, \
    ContactGroupMembers


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ContactAdmin(admin.ModelAdmin):
    list_display = ('msisdn',)


class SurveyResultsAdmin(admin.ModelAdmin):
    list_display = ('survey_id','msisdn','answer')


class ContactGroupAdmin(admin.ModelAdmin):
    list_display = ('name','created_by','created_at','rules')


class ContactGroupMemberAdmin(admin.ModelAdmin):
    list_display = ('group','contact')



admin.site.register(Survey, SurveyAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(SurveyResults, SurveyResultsAdmin)
admin.site.register(ContactGroup, ContactGroupAdmin)
admin.site.register(ContactGroupMembers, ContactGroupMemberAdmin)
