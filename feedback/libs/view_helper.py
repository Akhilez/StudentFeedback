import random
import string

from django.http import HttpResponse, Http404
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render, get_object_or_404
from django.core.signing import *

from StudentFeedback.settings import COORDINATOR_GROUP, CONDUCTOR_GROUP, DIRECTOR_GROUP
from analytics.libs import db_helper
from feedback.forms import LoginForm
from feedback.models import *


def get_slave(session):
    sessions = Session.objects.all().order_by('-timestamp')[:20]
    for sess in sessions:
        if sess.mastersession == session.session_id:
            return sess
    return None


def get_master_session(session):
    if session.mastersession is None:
        return session
    return Session.objects.get(session_id=session.mastersession)


def goto_questions_page(page_no, category='faculty'):
    if page_no is None:
        return redirect('/feedback/questions/')
    return redirect('/feedback/questions/' + category + '/?page=' + str(page_no))


def get_cur_time_offset(session):
    # how long has it been since the session started?
    current_time = datetime.datetime.now(datetime.timezone.utc)
    session_time = session.timestamp
    difference = (current_time - session_time).total_seconds() / 60 - 30
    return difference


def get_todays_initiations():
    all_initiations = Initiation.objects.all()
    initiations_list = []
    for initiation in all_initiations:
        if initiation.timestamp.date() == datetime.date.today():
            initiations_list.append(initiation)
    return initiations_list


def feedback_running(request):
    return request.session.get('sessionObj') is not None


def goto_max_page(request):
    max_page = request.session.get('maxPage', [1, 'faculty'])
    return goto_questions_page(max_page[0], max_page[1])


def invalid_user_page(request):
    return render(request, 'feedback/invalid_user.html')
































