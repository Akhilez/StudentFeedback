from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .libs import tree_builder


@login_required
def director(request):
    template = 'analytics/director.html'
    context = {}

    context['year_objs'] = tree_builder.getTree()

    return render(request, template, context)