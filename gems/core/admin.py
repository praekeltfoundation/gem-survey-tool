from django.contrib import admin
from .models import *


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name', 'survey_id', 'created_on', "series")
    search_fields = ("created_on", "name", "series")


class ContactAdmin(admin.ModelAdmin):
    list_display = ('msisdn', "created_on")
    search_fields = ("msisdn", "created_on")


class SurveyResultAdmin(admin.ModelAdmin):
    list_display = ("survey", "contact", "created_at", "updated_at", "answer", "sent")
    search_fields = ("survey__name", "contact__msisdn", "created_at", "updated_at")


class RawSurveyResultAdmin(SurveyResultAdmin):
    pass


class IncomingSurveyAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "raw_message")
    search_fields = ("timestamp", "raw_message")


class ContactGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'group_key', 'created_by', 'created_at', 'query_words', 'filters')
    search_fields = ("name", "group_key", "query_words", "filters")


class ContactGroupMemberAdmin(admin.ModelAdmin):
    list_display = ('group', 'contact')
    search_fields = ("group__name", "contact__msisdn")


class ExportTypeMappingAdmin(admin.ModelAdmin):
    list_display = ('field', 'cast')


class SettingAdmin(admin.ModelAdmin):
    list_display = ("name", "value")
    search_fields = ("name", "value")


class SentMessageAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'total')

    def has_add_permission(self, request):
        return False


admin.site.register(Survey, SurveyAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(SurveyResult, SurveyResultAdmin)
admin.site.register(ContactGroup, ContactGroupAdmin)
admin.site.register(ContactGroupMember, ContactGroupMemberAdmin)
admin.site.register(ExportTypeMapping, ExportTypeMappingAdmin)
admin.site.register(RawSurveyResult, RawSurveyResultAdmin)
admin.site.register(IncomingSurvey, IncomingSurveyAdmin)
admin.site.register(Setting, SettingAdmin)
admin.site.register(SentMessage, SentMessageAdmin)