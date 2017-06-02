import random
import string

from django.http import HttpResponse, Http404
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render, get_object_or_404
from django.core.signing import *

from StudentFeedback.settings import COORDINATOR_GROUP, CONDUCTOR_GROUP, DIRECTOR_GROUP
from analytics.libs import db_helper
from feedback.forms import LoginForm
from feedback.models import *

__author__ = 'Akhil'


def goto_user_page(user):
    if user.groups.filter(name=COORDINATOR_GROUP).exists():
        return redirect('/feedback/initiate/')
    elif user.groups.filter(name=CONDUCTOR_GROUP).exists():
        return redirect('/feedback/conduct/')
    elif user.groups.filter(name=DIRECTOR_GROUP).exists():
        return redirect('/analytics/')
    elif user.is_superuser:
        return redirect('/admin/')
    elif user.is_authenticated():
        return HttpResponse("You are not assigned any group. Contact the system admin.")
    return HttpResponse("You are already logged in")


def login_result(request, template, context):
    form = LoginForm(request.POST)
    if form.is_valid():
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return goto_user_page(user)
        else:
            context['error'] = 'login error'
        context['form'] = form

    return render(request, template, context)
