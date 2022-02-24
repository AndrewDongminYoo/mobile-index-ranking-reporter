from django import forms

from crawler.models import App, Following


class AppChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: App):
        return obj.app_name


class FollowingChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Following):
        return obj.app_name
