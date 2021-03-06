"""StudentFeedback URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from feedback import views
from django.contrib.auth.views import login, logout

urlpatterns = [
    url(r'^$', views.login_redirect, name='login_redirect'),
    url(r'^feedback/', include('feedback.urls', namespace='feedback')),
    url(r'^analytics/', include('analytics.urls', namespace='analytics')),
    url(r'^admin/', admin.site.urls),
    url(r'^login/$', views.login_view, name='login_view'),
    url(r'^logout/$', logout, {'next_page': '/login'}),
]
