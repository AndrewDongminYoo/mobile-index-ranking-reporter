from django import forms
from django.utils.translation import gettext_lazy as _

from crawler.models import App, Following


class AppChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: App):
        return obj.app_name


class AppCreateForm(forms.ModelForm):
    class Meta:
        model = Following
        fields = ["app_name", "package_name", "market_appid"]
        labels = {
            "app_name": _("App Name"),
            "package_name": _("Package"),
            "market_appid": _("APPID"),
        }
        widgets = {
            "app_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "애플리케이션 이름"}),
            "package_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "스토어 패키지이름"}),
            "market_appid": forms.TextInput(attrs={"class": "form-control", "placeholder": "원스토어 앱아이디"}),
        }

