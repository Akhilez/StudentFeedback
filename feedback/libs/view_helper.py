from django.core.signing import *
from django.shortcuts import redirect, render

from feedback.models import *


def get_slave_of(session):
    for sess in SlaveSession.objects.all():
        if sess.master == session:
            return sess.slave
    return None


def get_master_of(session):
    for sess in SlaveSession.objects.all():
        if sess.slave == session:
            return sess.master
    return None


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
    if request.session.get('sessionObj') is not None:
        if request.session.get('invalid_count') is None:
            request.session['invalid_count'] = 1
        else:
            request.session['invalid_count'] = request.session['invalid_count'] + 1
        if request.session['invalid_count'] > 2:
            del request.session['invalid_count']
            del request.session['sessionObj']
        else:
            return True
    return False


def invalid_user_page(request):
    return render(request, 'feedback/invalid_user.html')


def list_to_str(my_list):
    string = ""
    for item in my_list:
        string += item + ","
    return string[:-1]


def get_next_fdbk_response(request):
    fdbk_list = request.session.get('next_feedback')
    if fdbk_list is None or len(fdbk_list) == 0:
        del request.session['sessionObj']
        del request.session['maxPage']
        del request.session['next_feedback']
        return redirect('http://' + request.META['HTTP_HOST'][:-5] + '/survey/Thank.py')
    fdbk_list = fdbk_list.split(",")

    if fdbk_list[0] == 'fe':
        if len(fdbk_list) == 1:
            del request.session['sessionObj']
            del request.session['maxPage']
            del request.session['next_feedback']
        response = redirect('http://' + request.META['HTTP_HOST'][:-5] + '/')
        response.set_cookie('class_id', request.session.get('classId'))
        if len(fdbk_list) > 1:
            response.set_cookie('next_link', fdbk_list[1])
            request.session['next_feedback'] = list_to_str(fdbk_list[1:])
        else:
            response.set_cookie('next_link', 'thankYouPage')
            request.session['next_feedback'] = ''
        return response

    request.session['next_feedback'] = list_to_str(fdbk_list[1:]) if len(fdbk_list) > 0 else ''

    return redirect('/feedback/questions' if fdbk_list[0] == 'fa' else '/feedback/LoaQuestions')
