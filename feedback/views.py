from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect
from StudentFeedback.settings import COORDINATOR_GROUP, CONDUCTOR_GROUP, LOGIN_URL
from feedback.forms import LoginForm, InitiateForm
from django.contrib.auth.decorators import login_required
from feedback.models import Classes


def login_redirect(request):
    return redirect(LOGIN_URL)


def login_view(request):
    if request.user.is_authenticated:
        return goto_user_page(request.user)
    template = "login.html"
    context = {}
    if request.method == "POST":
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
    else:
        context['form'] = LoginForm()
    return render(request, template, context)


def goto_user_page(user):
    if user.groups.filter(name=COORDINATOR_GROUP).exists():
        return redirect('/feedback/initiate/')
    elif user.groups.filter(name=CONDUCTOR_GROUP).exists():
        return redirect('/feedback/conduct/')
    elif user.is_superuser:
        return redirect('/admin/')
    return HttpResponse("You are already logged in")


@login_required
def initiate(request, year, branch, section):
    if not request.user.groups.filter(name=COORDINATOR_GROUP).exists():
        return HttpResponse("You don't have permissions to view this page")
    context = {}
    template = 'feedback/initiate.html'
    years = Classes.objects.order_by('year').values_list('year').distinct()
    context['years'] = years
    if year != '':
        context['selectedYear'] = year
        branches = Classes.objects.filter(year=year).values_list('branch').order_by('branch').distinct()
        context['branches'] = branches
    if branch != '0':
        context['selectedBranch'] = branch
        sections = Classes.objects\
            .filter(year=year, branch=branch)\
            .values_list('section')\
            .order_by('section')\
            .distinct()
        context['sections'] = sections
    if section != '0':
        context['selectedSection'] = section
        #Do whatever we do with the selected class here!

    if request.method == "POST":
        form = InitiateForm(request.POST)
        if form.is_valid():
            user = request.POST['user']
            '''if user is not None:
                login(request, user)
                return goto_user_page(user)
            else:
                context['error'] = 'login error'
            context['form'] = form'''
    else:
        context['form'] = InitiateForm()
    return render(request, template, context)



@login_required
def conduct(request):
    if not request.user.groups.filter(name=CONDUCTOR_GROUP).exists():
        return HttpResponse("You don't have permissions to view this page")
    return render(request, 'feedback/conduct.html')
