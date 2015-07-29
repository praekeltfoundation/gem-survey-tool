from django import forms


class SurveyImportForm(forms.Form):
    file = forms.FileField()
