from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required


@login_required
def director(request):
    template = 'analytics/director.html'
    context = {}

    return render(request, template, context)