import random
import string

from django.http import HttpResponse, Http404
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render, get_object_or_404
from django.core.signing import *

from StudentFeedback.settings import COORDINATOR_GROUP, CONDUCTOR_GROUP, DIRECTOR_GROUP
from analytics.libs import db_helper
from feedback.forms import LoginForm
from feedback.libs.config_helper import getStudentTimeout, get_session_length, getGracePeriod
from feedback.libs.view_helper import get_cur_time_offset
from feedback.models import *

__author__ = 'Akhil'


def not_conductor(request):
    groups = request.user.groups.all()
    return not groups.filter(name=CONDUCTOR_GROUP).exists()


def set_student_login_enabled_status(context, session):
    # get elapsed time = cur_time
    cur_time = get_cur_time_offset(session)
    if session.stutimeout > cur_time:
        context['warning'] = "The student login page is enabled!"
    else:
        context['success'] = "Enable the student page"


def get_editable_result(request, template, context, editable):
    # get session object
    session = get_object_or_404(Session, session_id=editable)

    # if there is no active session, return error page
    if get_cur_time_offset(session) > get_session_length():
        raise Http404

    context['otp'] = editable
    context['classSelected'] = session.initiation_id.class_id

    #set_student_login_enabled_status(context, session)
    '''
    if request.method == 'POST':
        if 'disableStuLogin' in request.POST:
            disable_student_login(editable, context)

        if 'enableStuLogin' in request.POST:
            enable_student_login(editable, context)
    '''

    return render(request, template, context)


def enable_student_login(editable, context):
    try:
        session = Session.objects.get(session_id=editable)
        session.stutimeout = get_cur_time_offset(session) + getGracePeriod()
        session.save()
        context['warning'] = "The student login page is enabled!"
        del context['success']
    except KeyError:
        pass


def disable_student_login(editable, context):
    try:
        session = Session.objects.get(session_id=editable)
        session.stutimeout = getStudentTimeout()
        session.save()
        context['success'] = "Enable the student page"
        del context['warning']
    except KeyError:
        pass


def add_classes_for_session_selection(context):
    # get initiations for which session is not taken.
    initlist = get_init_for_no_session()
    if len(initlist) != 0:
        context['classes'] = initlist


def add_my_sessions(user, context):
    # get all sessions started by the user
    allSessions = Session.objects.filter(taken_by=user).order_by('-timestamp')[:15]

    running_sessions = []

    for session in allSessions:
        cur_time = get_cur_time_offset(session)
        if session.timestamp.date() == datetime.date.today() and get_session_length() > cur_time:
            running_sessions.append(session.session_id)

    context['allSessions'] = allSessions
    context['running'] = running_sessions


def get_init_for_sessions():
    sessionsList = []
    allSessions = Session.objects.all().order_by('-timestamp')
    for session in allSessions:
        if session.timestamp.date() == datetime.date.today():
            if not session.master:
                sessionsList.append(session.initiation_id)
    return sessionsList


def get_init_for_no_session():
    # get initiations for which session is not taken
    allInits = Initiation.objects.all()
    initlist = []
    for i in allInits:
        if i.timestamp.date() == datetime.date.today():
            if i not in get_init_for_sessions():
                initlist.append(i)
    return initlist


def confirm_session_result(request):
    # is the session required to split? if yes, the current session is master
    split = request.POST.getlist('master')
    if len(split) > 0:
        master = True
    else:
        master = False

    # get the class from session
    classFromSelect = request.session.get('class')

    # get the attendance
    checkValues = request.POST.getlist("attendanceList")

    # generate otp
    otp = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    dt = str(datetime.datetime.now())

    # get the initiation obj from selected class
    initObj = None
    for init in get_init_for_no_session():
        if str(init.class_id.class_id) == str(classFromSelect):
            initObj = init
            break

    # check if session exists
    allSessions = Session.objects.all().order_by('-timestamp')
    masterSession = None
    alreadyThere = False
    for session0 in allSessions:
        if initObj == session0.initiation_id:
            masterSession = session0
            alreadyThere = True
            break

    # insert new session record
    if not alreadyThere:
        session = Session.objects.create(timestamp=dt, taken_by=request.user, initiation_id=initObj,
                                         session_id=otp, master=master,
                                         stutimeout=getStudentTimeout())
    else:
        masterSession.master = False
        masterSession.save()
        session = Session.objects.create(timestamp=dt, taken_by=request.user, initiation_id=initObj,
                                         session_id=otp, master=False, mastersession=masterSession.session_id,
                                         stutimeout=getStudentTimeout())

    # insert the attendance into table
    for htno in checkValues:
        Attendance.objects.create(student_id=Student.objects.get(hallticket_no=htno), session_id=session)

    return redirect('/')



def take_attendance_result(request, template, context):

    # get the class obj from the dropdown
    classFromSelect = request.POST.getlist('selectClass')[0]
    classObj = Classes.objects.get(class_id=classFromSelect)

    # set the context and session with class
    context['classSelected'] = classObj
    request.session['class'] = classObj.class_id

    alreadyThere = False

    # get the initiation object of the selected class
    initObj = None
    for init in get_init_for_no_session():
        if str(init.class_id.class_id) == str(classFromSelect):
            initObj = init
            break

    # check if there are any sessions with the initiation id, if yes, is it a master session?
    allSessions = Session.objects.all().order_by('-timestamp')
    masterSession = None
    for session in allSessions:
        if initObj == session.initiation_id:
            if session.master:
                alreadyThere = True
                masterSession = session
                context['master'] = True
            break

    # get all the student roll numbers for attendance
    allStudents = Student.objects.filter(class_id=classObj)
    if alreadyThere:
        absentStudents = []
        presentStudentsList = []
        presentStudents = Attendance.objects.filter(session_id=masterSession)
        for pS in presentStudents: presentStudentsList.append(pS.student_id)
        for student in allStudents:
            if student not in presentStudentsList:
                absentStudents.append(student)
        allStudents = absentStudents

    context['allStudetns'] = allStudents
    return render(request, template, context)