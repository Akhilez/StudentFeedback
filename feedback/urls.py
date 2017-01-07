from feedback import views

__author__ = 'Akhil'

from django.conf.urls import url
from django.contrib import admin


urlpatterns = [
    url(r'^login/$', views.login, name="login"),
]