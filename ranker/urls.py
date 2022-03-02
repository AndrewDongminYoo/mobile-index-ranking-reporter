"""ranker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from crawler.rank.api1 import api as api1
from crawler.rank.api2 import api as api2
from crawler.rank.views import index, rank
from .settings import STATIC_URL, STATIC_ROOT

urlpatterns = [
    path("", index),
    path("rank/", rank),
    # path("ranking", ranking),
    # path("register", app_register),
    # path("statistic/<str:market>/<str:deal>/<str:app>", statistic),
    # path("my_rank", my_rank, name="my_rank"),
    path('admin/', admin.site.urls),
    path("v1/", api1.urls),
    path("v2/", api2.urls)
] + static(STATIC_URL, document_root=STATIC_ROOT)
