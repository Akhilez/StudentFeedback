__author__ = 'Akhil'

from analytics import views

from django.conf.urls import url


urlpatterns = [
    url(r'^$', views.director, name="director"),
]