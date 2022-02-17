from django import forms

from crawler.models import App


class AppChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: App):
        return obj.app_name
