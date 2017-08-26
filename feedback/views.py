from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from analytics.libs import db_updater
from feedback.libs.views import login_view_helper, initiate_view, conduct_view, late_login_view, student_view, \
    questions_view, change_pass_view, loa_questions_view, forgot_password_view
from feedback.models import ClassFacSub


def login_redirect(request):
    return login_view_helper.get_redirect(request)


def login_view(request):
    return login_view_helper.get_view(request)


@login_required
def initiate(request):
    return initiate_view.get_view(request)


@login_required
def conduct(request):
    return conduct_view.get_view(request)


@login_required()
def latelogin(request, session_id):
    return late_login_view.get_view(request, session_id)


def student(request):
    return student_view.get_view(request)


def questions(request):
    return questions_view.get_view(request)


@login_required
def changepass(request):
    return change_pass_view.get_view(request)


def LoaQuestions(request):
    return loa_questions_view.get_view(request)


def display_cfs(request):
    template = 'feedback/updatedb.html'
    context = {'classes': ClassFacSub.objects.all()}
    return render(request, template, context)


def updatedb(request):
    template = 'feedback/updatedb.html'
    context = {}
    data = None

    # data = db_updater.update_classes()
    # data = db_updater.update_students()
    # data = db_updater.update_faculty()
    # data = db_updater.update_subjects()
    # data = db_updater.update_class_fac_sub()
    # data = db_updater.update_faculty_questions()
    # data = db_updater.update_loa_questions()
    # data = db_updater.update_faculty_names()
    #data = db_updater.update_cfs_names()

    #context['submit'] = 'update_faculty_names'
    #context['submit'] = 'update_cfs_names'

    if request.method == "POST":
        if 'update_faculty_names' in request.POST:
            data = db_updater.update_faculty_names(True)
            del context['submit']
        if 'update_cfs_names' in request.POST:
            data = db_updater.update_cfs_names(True)
            del context['submit']

    context['classes'] = data

    return render(request, template, context)


def forgotPassword(request):
    return forgot_password_view.get_view(request)
