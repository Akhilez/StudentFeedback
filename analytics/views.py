from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .libs import tree_builder
from StudentFeedback.settings import DIRECTOR_GROUP


@login_required
def director(request, category, year, branch, sub, subsub):

    if not request.user.groups.filter(name=DIRECTOR_GROUP).exists():
        return render(request, 'feedback/invalid_user.html')

    template = 'analytics/director.html'
    context = {}

    context['year_objs'] = tree_builder.getTree()

    itr = 0
    if category == 'class':
        if len(year) == 0:
            itr = 1
        elif len(branch) == 0:
            itr = 2
        elif len(sub) == 0:
            itr = 3
        else:
            itr = 4
        context['category'] = category

    elif category == 'fac':
        if len(subsub) == 0:
            itr = 5
        else:
            itr = 6
        context['category'] = category

    elif category == 'stu':
        if len(year) == 0:
            itr = 7
        elif len(branch) == 0:
            itr = 8
        elif len(sub) == 0:
            itr = 9
        else:
            itr = 10
        context['category'] = category

    else:
        context['category'] = 'None'

    context['itr'] = itr
    context['year'] = year

    return render(request, template, context)