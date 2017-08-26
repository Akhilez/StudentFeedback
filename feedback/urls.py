from django.conf.urls import url
from feedback import views

urlpatterns = [
    url(r'^$', views.login_redirect, name="login_redirect"),
    url(r'^initiate/$', views.initiate, name="initiate"),
    url(r'^conduct/$', views.conduct, name="conduct"),
    url(r'^student/$', views.student, name="student"),
    url(r'^questions/$', views.questions, name="questions"),
    url(r'^latelogin/(\w+)/$', views.latelogin, name="latelogin"),
    url(r'^changepass/$', views.changepass, name="changepass"),
    url(r'^LoaQuestions/$', views.LoaQuestions, name="LoaQuestions"),
    url(r'^updatedb/$', views.updatedb, name='updatedb'),
    url(r'^forgotPassword/$', views.forgotPassword, name='updatedb'),
    url(r'^displayCfs/$', views.display_cfs, name="displayCfs"),
]