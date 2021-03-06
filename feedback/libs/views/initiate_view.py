import datetime

from django.shortcuts import redirect, render

from StudentFeedback.settings import COORDINATOR_GROUP
from analytics.libs import db_helper
from feedback.libs import view_helper
from feedback.models import *

__author__ = 'Akhil'


def get_view(request):
    if view_helper.feedback_running(request):
        return redirect('/feedback/questions/')

    if not_coordinator(request):
        return view_helper.invalid_user_page(request)

    template = 'feedback/initiate.html'
    context = {'active': 'home'}

    # adding history - recent initiations and sessions
    add_history(context)

    # filling classes table with years
    context['years'] = db_helper.get_years()

    # handling the submit buttons
    if request.method == 'POST':
        if 'nextSection' in request.POST:
            return next_section_result(request, template, context)

        if 'confirmSelected' in request.POST:
            return confirm_selected_class_result(request, template, context)

    return render(request, template, context)


def not_coordinator(request):
    groups = request.user.groups.all()
    return not groups.filter(name=COORDINATOR_GROUP).exists()


def add_history(context):
    context['total_history'] = Initiation.objects.all().order_by('-timestamp')[:10]
    context['recent_feedbacks'] = Session.objects.all().order_by('-timestamp')[:10]


def initiate_for(year, branch, section, by, feedback_of):
    classobj = Classes.objects.get(year=year, branch=branch, section=section)
    history = Initiation.objects.filter(class_id=classobj)
    if len(history) == 0 or history[len(history) - 1].timestamp.date() != datetime.date.today():
        dt = str(datetime.datetime.now())
        Initiation.objects.create(timestamp=dt, initiated_by=by, class_id=classobj, feedback_of=feedback_of)
        return True
    else:
        return False


def list_to_str(my_list):
    my_list.sort()
    string = ""
    for item in my_list:
        string += item[1:] + ","
    return string[:-1]


def confirm_selected_class_result(request, template, context):
    checked_list = request.POST.getlist('class')
    feedback_of = list_to_str(request.POST.getlist('class2'))
    success_lst = []
    for i in checked_list:
        inst = i.split('-')
        status = initiate_for(inst[0], inst[1], inst[2], request.user, feedback_of)
        if status:
            success_lst.append(inst[0] + "-" + inst[1] + "-" + inst[2])
    context['success_status'] = success_lst
    return render(request, template, context)


def is_not_eligible(cls):
    initiations = Initiation.objects.all()
    for initiation in initiations:
        if initiation.timestamp.date() == datetime.date.today():
            if cls == initiation.class_id:
                return True
    return False


def get_not_eligible(classes_of_years):
    not_eligible = []
    for i in range(len(classes_of_years)):
        if is_not_eligible(classes_of_years[i]):  # already initiated
            not_eligible.append(i + 1)
    return not_eligible


def get_classes_of_years(selected_years, my_branches):
    classes_of_years = []
    all_classes = Classes.objects.all().order_by('year')
    for yr in selected_years:
        my_year = all_classes.filter(year=db_helper.deformatter[yr])
        for myYr in my_year:
            for myBranch in my_branches:
                if myYr.branch == myBranch:
                    classes_of_years.append(myYr)
                    break
    return classes_of_years


def get_coordinator_branches(user):
    groups = user.groups.all()
    my_branches = []
    for group in groups:
        if group.name != COORDINATOR_GROUP:
            my_branches.append(group.name)
    return my_branches


def next_section_result(request, template, context):
    selected_years = request.POST.getlist('class')
    my_branches = get_coordinator_branches(request.user)

    classes_of_years = get_classes_of_years(selected_years, my_branches)

    context['myClasses'] = classes_of_years
    context['not_eligible'] = get_not_eligible(classes_of_years)

    return render(request, template, context)
