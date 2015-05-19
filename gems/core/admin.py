from django.contrib import admin
from models import Survey, Contact, SurveyResult, ContactGroup, ContactGroupMember, ExportTypeMapping


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name', 'survey_id', 'created_on')


class ContactAdmin(admin.ModelAdmin):
    list_display = ('msisdn',)


class SurveyResultAdmin(admin.ModelAdmin):
    list_display = ('survey', 'contact', 'answer', 'sent')


class ContactGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'group_key', 'created_by', 'created_at', 'query_words', 'filters')


class ContactGroupMemberAdmin(admin.ModelAdmin):
    list_display = ('group', 'contact')


class ExportTypeMappingAdmin(admin.ModelAdmin):
    list_display = ('field', 'cast')


admin.site.register(Survey, SurveyAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(SurveyResult, SurveyResultAdmin)
admin.site.register(ContactGroup, ContactGroupAdmin)
admin.site.register(ContactGroupMember, ContactGroupMemberAdmin)
admin.site.register(ExportTypeMapping, ExportTypeMappingAdmin)
