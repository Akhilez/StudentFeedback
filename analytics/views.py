from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from analytics.libs.drilldown_chart import Graphable
from .libs import tree_builder, graph_builder
from StudentFeedback.settings import DIRECTOR_GROUP
from analytics.libs import db_helper, faculty_graph


@login_required
def director(request, category, year, branch, sub, subsub):

    if not request.user.groups.filter(name=DIRECTOR_GROUP).exists():
        return render(request, 'feedback/invalid_user.html')

    template = 'analytics/director.html'
    context = {'category': category, 'year': year, 'branch': branch, 'sub': sub, 'subsub': subsub,
               'year_objs': tree_builder.getTree(), 'active': 'home'}
    graph_type = 'null'
    if request.method == 'POST':
        for typ in graph_builder.Graph.types:
            if typ in request.POST:
                graph_type = typ
                break

    context['graph'] = graph_builder.Graph(category, year, branch, sub, subsub, graph_type=graph_type)
    context['Drilldown'] = Graphable.drilldown

    context['facultys'] = db_helper.get_all_faculty()


    return render(request, template, context)


@login_required
def faculty_info(request):
    if request.method == 'POST':
        if 'faculty' in request.POST:

            context = {}
            faculty = request.POST.getlist('faculty')[0]

            context['faculty'] = faculty

            graph_type = 'null'
            if request.method == 'POST':
                for typ in graph_builder.Graph.types:
                    if typ in request.POST:
                        graph_type = typ
                        break

            context['graph'] = faculty_graph.FacultyGraph()

            return render(request, 'analytics/faculty.html', context)
    return HttpResponse("Error")