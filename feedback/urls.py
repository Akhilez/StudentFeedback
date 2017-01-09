from feedback import views

__author__ = 'Akhil'

from django.conf.urls import url
from django.contrib import admin


urlpatterns = [
    url(r'^$', views.login_redirect, name="login_redirect"),

    url(r'^initiate/(?P<year>[1-4])/(?P<branch>[a-zA-Z]+)/(?P<section>[a-zA-Z])/$', views.initiate, name="initiate"),
    url(r'^initiate/(?P<year>[1-4])/(?P<branch>[a-zA-Z]+)/()$', views.initiate, name="initiate"),
    url(r'^initiate/(?P<year>[1-4])/()()$', views.initiate, name="initiate"),
    url(r'^initiate/()()()$', views.initiate, name="initiate"),

    url(r'^conduct/$', views.conduct, name="conduct"),
]