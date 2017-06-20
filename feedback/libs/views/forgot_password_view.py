from django.core.mail import EmailMessage
from django.shortcuts import render

__author__ = 'Akhil'


def get_view(request):
    template = 'feedback/forgotPassword.html/'
    email = EmailMessage('hii', 'hiiiiii', to=['rajrocksdeworld@gmail.com'])
    email.send()
    return render(request, template, {})