from django import forms

from crawler.models import App


class AppChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: App):
        return obj.app_name

    def get_limit_choices_to(self):
        return super().get_limit_choices_to()
