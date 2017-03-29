from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from analytics.libs.db_helper import Timeline

from feedback.models import *
from .libs import tree_builder, graph_builder
from StudentFeedback.settings import DIRECTOR_GROUP
from analytics.libs import db_helper
from analytics.libs.faculty_graphs import faculty_graph, class_sub_graph, timeline_graph


@login_required
def index_view(request):
    return render(request, 'analytics/index.html', {})


def set_selected_questions(request):
    if 'select_ques' in request.POST:
        questions = request.POST.getlist('ques')
        Timeline.selected_questions = []
        for ques in questions:
            ques = ques[1:]
            Timeline.selected_questions.append(int(ques))


@login_required
def director(request, category, year, branch, sub, subsub):

    if not request.user.groups.filter(name=DIRECTOR_GROUP).exists():
        return render(request, 'feedback/invalid_user.html')

    template = 'analytics/director.html'
    context = {'category': category, 'year': year, 'branch': branch, 'sub': sub, 'subsub': subsub,
               'year_objs': tree_builder.getTree(), 'active': 'home'}

    set_selected_questions(request)

    graph_type = 'null'
    if request.method == 'POST':
        for typ in graph_builder.Graph.types:
            if typ in request.POST:
                graph_type = typ
                break

    context['graph'] = graph_builder.Graph(category, year, branch, sub, subsub, graph_type=graph_type)

    context['facultys'] = db_helper.get_all_faculty()

    context['all_questions'] = db_helper.get_all_question_texts()
    context['selected_indices'] = db_helper.get_selected_questions()

    return render(request, template, context)


@login_required
def faculty_info(request):

    if not request.user.groups.filter(name=DIRECTOR_GROUP).exists():
        return render(request, 'feedback/invalid_user.html')

    context = {}

    if request.method == 'POST':
        if 'faculty' in request.POST:
            faculty = request.POST.getlist('faculty')[0]
            request.session['faculty'] = faculty
        elif request.session.get('faculty') is not None:
            faculty = request.session.get('faculty')
        else:
            return redirect('/analytics/all')

        set_selected_questions(request)

        try:
            faculty = Faculty.objects.get(name=faculty)
        except:
            context['error'] = "Sorry, the faculty: "+faculty+' is not found'
            return render(request, 'analytics/faculty.html', context)

        context['faculty'] = faculty
        context['faculty_value'] = round(db_helper.get_faculty_value(faculty), 2)

        context['graph'] = faculty_graph.FacultyGraph(faculty=faculty.name)
        context['graph2'] = class_sub_graph.ClassSubGraph(faculty=faculty.name)
        context['graph3'] = timeline_graph.TimelineGraph(faculty=faculty.name)

        context['facultys'] = db_helper.get_all_faculty()
        context['all_questions'] = db_helper.get_all_question_texts()
        context['selected_indices'] = db_helper.get_selected_questions()

        return render(request, 'analytics/faculty.html', context)
    else:
        return redirect('/analytics/all')

@login_required
def reviews(request):
    template = 'analytics/reviews.html'
    context = []

    if 'submit' in request.POST:
        try:
            year = request.POST.get('year')
            branch = request.POST.get('branch')
            section = request.POST.get('section')
            cid = Classes.objects.get(year=year, branch=branch, section=section)
            initid = Initiation.objects.get(class_id=cid.class_id)
            sid = Session.objects.get(initiation_id=initid.initiation_id)
            notes = Notes.objects.all().filter(session_id=sid)
            context ={'year': year, 'branch':branch, 'section':section, 'notes':notes}
        except TypeError:
            context['error'] = 'Please Check if the class has completed their Review or not'



    '''if year:
        context ={'year': year, }
    if year and branch:
        allClasses = Classes.objects.all().filter(year=year,branch=branch)
        context = {'year': year, 'sections' : allClasses}
    if year and branch and section:
        cid = Classes.objects.get(year=year,branch=branch,section=section)
        initid = Initiation.objects.get(class_id=cid.class_id)
        sid = Session.objects.get(initiation_id=initid.initiation_id)
        notes = Notes.objects.get(session_id=sid)
        context = {'year': year, 'sections': allClasses, 'sid': notes}'''

    return render(request, template, context)
