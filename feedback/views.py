from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from feedback.forms import LoginForm


def login_redirect(request):
    return redirect('/feedback/login/')


def login_view(request):
    template = "login.html"
    context = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                pass
            else:
                pass
    return HttpResponse("Login")