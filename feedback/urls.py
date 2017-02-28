from feedback import views

from django.conf.urls import url
from django.contrib import admin


urlpatterns = [
    url(r'^$', views.login_redirect, name="login_redirect"),
    url(r'^initiate/$', views.initiate, name="initiate"),
    url(r'^conduct/()$', views.conduct, name="conduct"),
    url(r'^conduct/(\w+)/$', views.conduct, name="conduct"),
    url(r'^student/$', views.student, name="student"),
    url(r'^questions/()$', views.questions, name="questions"),
    url(r'^questions/(\w+)/$', views.questions, name="questions"),
    url(r'^latelogin/(\w+)/$', views.latelogin, name="latelogin"),
    url(r'^mysessions/$', views.mysessions, name="mysessions"),
    url(r'^changepass/$', views.changepass, name="changepass"),
]