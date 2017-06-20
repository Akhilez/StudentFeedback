from django.http import Http404
from django.shortcuts import redirect, get_object_or_404, render
from feedback.libs.config_helper import get_session_length
from feedback.libs.view_helper import feedback_running, get_cur_time_offset
from feedback.libs.views.conduct_view import get_absent_students
from feedback.models import Attendance, Student, Session

__author__ = 'Akhil'


def get_view(request, session_id):
    """
    1. get session from url
    2. if session invalid or expired, throw 404
    3. add absent students into context
    4. handle button event-
        a. get attendance from checkboxes
        b. insert attendance into attendance table
    :param request:
    :param session_id:
    :return: html response
    """
    if feedback_running(request):
        return redirect('/feedback/questions/')

    context = {}
    template = 'feedback/latelogin.html'

    # 1. get the session from session_id url
    session = get_object_or_404(Session, session_id=session_id)
    if get_cur_time_offset(session) > get_session_length():
        raise Http404

    if request.method == 'POST':
        attendance = request.POST.getlist('attendance')
        for stud in attendance:
            Attendance.objects.create(student_id=Student.objects.get(hallticket_no=stud), session_id=session)

        return redirect('/feedback/conduct')

    context['session'] = session
    context['students'] = get_absent_students(session)

    return render(request, template, context)
