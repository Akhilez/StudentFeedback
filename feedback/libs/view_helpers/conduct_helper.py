import random
import string

from django.http import HttpResponse, Http404
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render, get_object_or_404
from django.core.signing import *

from StudentFeedback.settings import COORDINATOR_GROUP, CONDUCTOR_GROUP, DIRECTOR_GROUP
from analytics.libs import db_helper
from feedback.forms import LoginForm
from feedback.libs.config_helper import get_session_length
from feedback.libs.view_helper import get_cur_time_offset, get_master_of, get_slave_of
from feedback.models import *

__author__ = 'Akhil'


def not_conductor(request):
    groups = request.user.groups.all()
    return not groups.filter(name=CONDUCTOR_GROUP).exists()


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


def add_classes_for_session_selection(context):
    # get initiations for which session is not taken.
    initlist = get_init_for_no_session()
    if len(initlist) != 0:
        context['classes'] = initlist


def make_master_result(session):
    SlaveSession.objects.create(master=Session.objects.get(session_id=session))
    return redirect('/')


def add_my_sessions(user, context):
    # get all sessions started by the user
    allSessions = Session.objects.filter(taken_by=user).order_by('-timestamp')[:15]

    running_sessions = []
    running_masters = []

    for session in allSessions:
        cur_time = get_cur_time_offset(session)
        if session.timestamp.date() == datetime.date.today() and get_session_length() > cur_time:
            running_sessions.append(session.session_id)
            try:
                SlaveSession.objects.get(master=session)
            except:
                running_masters.append(session.session_id)

    context['allSessions'] = allSessions
    context['running'] = running_sessions
    context['running_masters'] = running_masters


def is_master(session):
    for sess in SlaveSession.objects.all():
        if sess.master == session and sess.slave is None:
            return True
    return False


def get_init_for_sessions():
    sessionsList = []
    allSessions = Session.objects.all().order_by('-timestamp')
    for session in allSessions:
        if session.timestamp.date() == datetime.date.today():
            if not is_master(session):
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
    master = True if len(request.POST.getlist('master')) > 0 else False

    # generate otp
    otp = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    dt = str(datetime.datetime.now())

    # get the initiation obj from selected class
    initObj = None
    for init in get_init_for_no_session():
        if str(init.class_id.class_id) == str(request.session.get('class')):
            initObj = init
            break

    # insert new session record
    session = Session.objects.create(timestamp=dt, taken_by=request.user, initiation_id=initObj, session_id=otp)

    if master:
        SlaveSession.objects.create(master=session)
    else:
        # check if session exists
        for session0 in Session.objects.all().order_by('-timestamp'):
            if initObj == session0.initiation_id and session != session0:
                master_session = SlaveSession.objects.get(master=session0)
                master_session.slave = session
                master_session.save()
                break

    # insert the attendance into table
    for htno in request.POST.getlist("attendanceList"):
        Attendance.objects.create(student_id=Student.objects.get(hallticket_no=htno), session_id=session)

    return redirect('/')


def get_session_for_running_class(classObj):
    """
    1. get initiation for the class
    2. get session for the initiation
    :param classObj:
    :return: session
    """

    # 1. get the initiation object of the selected class
    initObj = None
    for init in get_init_for_no_session():
        if init.class_id.class_id == classObj.class_id:
            initObj = init
            break

    # 2. get session for the initiation
    for session in Session.objects.all().order_by('-timestamp'):
        if initObj == session.initiation_id:
            return session


def get_absent_students(session):
    absentStudents = []
    presentStudentsList = []
    presentStudents = Attendance.objects.filter(session_id=session)
    for pS in presentStudents: presentStudentsList.append(pS.student_id)
    for student in Student.objects.filter(class_id=session.initiation_id.class_id):
        if student not in presentStudentsList:
            absentStudents.append(student)
    return absentStudents


def take_attendance_result(request, template, context):
    """
    1. get the class from drop down
    2. if session is slave session, add absent students to context
    3. else add all students to the context
    :param request:
    :param template:
    :param context:
    :return: context
    """

    # 1. get the class obj from the dropdown
    classObj = Classes.objects.get(class_id=request.POST.getlist('selectClass')[0])

    # set the context and session with class
    context['classSelected'] = classObj
    request.session['class'] = classObj.class_id

    # 2. if session is slave session, add absent students to context
    session = get_session_for_running_class(classObj)
    if session is not None and session.master:
        context['master'] = True
        context['allStudetns'] = get_absent_students(session)

    # 3. else add all students to the context
    else:
        context['allStudetns'] = Student.objects.filter(class_id=classObj)

    return render(request, template, context)


def filter_attendance(session, presentStudents):
    for attendance in Attendance.objects.filter(session_id=session):
        for student in presentStudents:
            if attendance.student_id == student:
                presentStudents.remove(student)


def get_absent_students_for_late_login(session):
    """
    1. get all students
    2. filter attendance form session
    3. filter attendance from master session
    3.1 filter attendance from slave session
    5. return the remaining students
    :param session:
    :return:
    """
    # 1. get all students
    students = [x for x in Student.objects.filter(class_id=session.initiation_id.class_id)]

    # 2. filter attendance form session
    filter_attendance(session, students)

    # 3. filter attendance from master session
    master = get_master_of(session)
    if master is not None:
        filter_attendance(master, students)

    # 3.1 filter attendance from slave session
    slave = get_slave_of(session)
    if slave is not None:
        filter_attendance(slave, students)

    return students