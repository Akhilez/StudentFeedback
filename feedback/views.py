from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from feedback.forms import LoginForm


def login_redirect(request):
    return redirect('/feedback/login/')


def login_view(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Coordinators').exists():
            return redirect('/feedback/initiate/')
        elif request.user.groups.filter(name='Coordinators').exists():
            return redirect('/feedback/conduct/')
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
                if user.groups.filter(name='Coordinators').exists():
                    return redirect('/feedback/initiate/')
                elif request.user.groups.filter(name='Coordinators').exists():
                    return redirect('/feedback/conduct/')
            else:
                context['error'] = 'login error'
            context['form'] = form
    else:
        context['form'] = LoginForm()
    return render(request, template, context)


def initiate(request):
    return render(request, 'feedback/initiate.html')


def conduct(request):
    return render(request, 'feedback/conduct.html')