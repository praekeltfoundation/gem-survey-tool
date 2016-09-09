from django import forms


class SurveyImportForm(forms.Form):
    email_address = forms.EmailField()
    file = forms.FileField()
