from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from analytics.libs.db_helper import Timeline
from feedback.models import *
from .libs import tree_builder, graph_builder
from StudentFeedback.settings import DIRECTOR_GROUP
from analytics.libs import db_helper, LOAgraph_builder, LOAtree_builder, LOAdb_helper
from analytics.libs.faculty_graphs import faculty_graph, class_sub_graph, timeline_graph


@login_required
def index_view(request):
    return render(request, 'analytics/index.html', {})


def set_selected_questions(request):
    if 'select_ques' in request.POST:
        questions = request.POST.getlist('ques')
        selected_questions = []
        for ques in questions:
            ques = ques[1:]
            selected_questions.append(int(ques))
        Timeline.set_selected_questions(selected_questions)


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
    context['selected_indices'] = db_helper.Timeline.get_selected_questions()

    return render(request, template, context)


@login_required
def faculty_info(request, faculty):
    if not request.user.groups.filter(name=DIRECTOR_GROUP).exists():
        return render(request, 'feedback/invalid_user.html')

    context = {}

    faculty = get_object_or_404(Faculty, faculty_id=faculty)

    set_selected_questions(request)

    context['faculty'] = faculty
    context['faculty_value'] = round(db_helper.get_faculty_value(faculty), 2)

    context['graph'] = faculty_graph.FacultyGraph(faculty=faculty.name)
    context['graph2'] = class_sub_graph.ClassSubGraph(faculty=faculty.name)
    context['graph3'] = timeline_graph.TimelineGraph(faculty=faculty.name)

    context['facultys'] = db_helper.get_all_faculty()
    context['all_questions'] = db_helper.get_all_question_texts()
    context['selected_indices'] = db_helper.Timeline.get_selected_questions()

    return render(request, 'analytics/faculty.html', context)


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
            context = {'year': year, 'branch': branch, 'section': section, 'notes': notes}
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


def LOAanalysis(request, category, year, branch, sub, subsub):
    template = 'analytics/LOAanalyis.html'
    context = {'category': category, 'year': year, 'branch': branch, 'sub': sub, 'subsub': subsub,
               'year_objs': LOAtree_builder.getTree(), 'active': 'home'}
    graph_type = 'null'
    if request.method == 'POST':
        for typ in LOAgraph_builder.Graph.types:
            if typ in request.POST:
                graph_type = typ
                break

    context['graph'] = LOAgraph_builder.LoaGraph(category, year, branch, sub, subsub, graph_type=graph_type)

    return render(request, template, context)


def get_csv(request, class_name):
    template = "analytics/get_csv.html"

    ratings_list = ["-------------------Learning outcome assessment----------------------"]
    ratings_list_faculty = ["-------------------FACULTY----------------------"]

    for cls in Classes.objects.filter(branch=class_name):
        for initiation in Initiation.objects.filter(class_id=cls):
            for session in Session.objects.filter(initiation_id=initiation):
                for feedback in FeedbackLoa.objects.filter(session_id=session):
                    subject_name = Subject.objects.get(subject_id=feedback.relation_id).name
                    ratings_list.append(str(str(cls)+","+subject_name+","+str(session.timestamp.date())+","+str(feedback.loaratings)))
                for feedback in Feedback.objects.filter(session_id=session):
                    subject_name = ClassFacSub.objects.get(cfs_id=feedback.relation_id).subject_id.name
                    ratings_list_faculty.append(str(str(cls)+","+str(subject_name)+","+str(session.timestamp.date())+","+str(feedback.ratings)))

    context = {'ratings_list': ratings_list, 'ratings_list_faculty': ratings_list_faculty}

    file = open('ratings.csv', 'w')
    for ratings in ratings_list:
        file.write(ratings + "\n")
    for ratings in ratings_list_faculty:
        file.write(ratings + "\n")
    file.close()

    return render(request, template, context)