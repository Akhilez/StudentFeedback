__author__ = 'Akhil'

from analytics import views

from django.conf.urls import url


urlpatterns = [
    url(r'^faculty/', views.faculty_info, name="faculty_info"),
    url(r'^()()()()()$', views.director, name="director"),
    url(r'^(\w+)/()()()()$', views.director, name="director"),
    url(r'^(\w+)/(\w+)/()()()$', views.director, name="director"),
    url(r'^(\w+)/(\w+)/(\w+)/()()$', views.director, name="director"),
    url(r'^(\w+)/(\w+)/(\w+)/(\w+)/()$', views.director, name="director"),
    url(r'^(\w+)/(\w+)/(\w+)/(\w+)/(\w+)/$', views.director, name="director"),
]