from feedback import views

__author__ = 'Akhil'

from django.conf.urls import url
from django.contrib import admin


urlpatterns = [
    url(r'^$', views.login_redirect, name="login_redirect"),
    url(r'^initiate/$', views.initiate, name="initiate"),
    url(r'^conduct/$', views.conduct, name="conduct"),
]