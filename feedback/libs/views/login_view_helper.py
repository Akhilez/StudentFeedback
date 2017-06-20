from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import redirect, render
from StudentFeedback.settings import LOGIN_URL, COORDINATOR_GROUP, CONDUCTOR_GROUP, DIRECTOR_GROUP
from feedback.forms import LoginForm
from feedback.libs.view_helper import feedback_running, get_todays_initiations

__author__ = 'Akhil'


def get_view(request):
    if feedback_running(request):
        return redirect('/feedback/questions/')

    if request.user.is_authenticated:
        return goto_user_page(request.user)

    template = "login.html"
    context = {}

    if request.method == "POST":
        if 'login' in request.POST:
            return login_result(request, template, context)
    else:
        context['form'] = LoginForm()

    return render(request, template, context)


def get_redirect(request):
    # if any user already logged in, take to their homepage
    if request.user.is_authenticated():
        return goto_user_page(request.user)

    # is any initiation open? then go to student otp page.
    if len(get_todays_initiations()) > 0:
        return redirect('/feedback/student')

    return redirect(LOGIN_URL)


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