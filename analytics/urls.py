__author__ = 'Akhil'

from analytics import views

from django.conf.urls import url


urlpatterns = [
    url(r'^$', views.index_view, name='index_view'),
    url(r'^faculty/', views.faculty_info, name="faculty_info"),
    url(r'^all/()()()()()$', views.director, name="director"),
    url(r'^all/(\w+)/()()()()$', views.director, name="director"),
    url(r'^all/(\w+)/(\w+)/()()()$', views.director, name="director"),
    url(r'^all/(\w+)/(\w+)/(\w+)/()()$', views.director, name="director"),
    url(r'^all/(\w+)/(\w+)/(\w+)/(\w+)/()$', views.director, name="director"),
    url(r'^all/(\w+)/(\w+)/(\w+)/(\w+)/(\w+)/$', views.director, name="director"),
    url(r'^reviews/', views.reviews, name="reviews"),

]