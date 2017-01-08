from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect
from feedback.forms import LoginForm
from django.contrib.auth.decorators import login_required


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


@login_required
def initiate(request):
    if not request.user.groups.filter(name='Coordinators').exists():
        return HttpResponse("You don't have permissions to view this page")
    return render(request, 'feedback/initiate.html')


@login_required
def conduct(request):
    if not request.user.groups.filter(name='Conductors').exists():
        return HttpResponse("You don't have permissions to view this page")
    return render(request, 'feedback/conduct.html')