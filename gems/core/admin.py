from django.contrib import admin
from models import Survey, Contact, SurveyResult, ContactGroup, ContactGroupMember


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ContactAdmin(admin.ModelAdmin):
    list_display = ('msisdn',)


class SurveyResultAdmin(admin.ModelAdmin):
    list_display = ('survey','contact','answer')


class ContactGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'group_key', 'created_by','created_at','query_words', 'filters')


class ContactGroupMemberAdmin(admin.ModelAdmin):
    list_display = ('group','contact')



admin.site.register(Survey, SurveyAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(SurveyResult, SurveyResultAdmin)
admin.site.register(ContactGroup, ContactGroupAdmin)
admin.site.register(ContactGroupMember, ContactGroupMemberAdmin)
