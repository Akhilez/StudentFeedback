from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.




def login_redirect(request):
    return redirect('/feedback/login/')


def login(request):
    return HttpResponse("Login")