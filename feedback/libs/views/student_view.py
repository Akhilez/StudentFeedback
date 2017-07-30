from django.shortcuts import redirect, render

from feedback.libs import view_helper
from feedback.libs.view_helper import feedback_running
from feedback.libs.views import questions_view
from feedback.models import Session

__author__ = 'Akhil'


def get_view(request):
    """
    1. get otp from text box
    2. validate from session table
    3. validate attendance
    4. Start a django session and redirect to the feedback questions page
    :param request:
    :return: http response
    """
    if feedback_running(request):
        return redirect('/feedback/questions/')

    template = 'feedback/student_login.html'
    context = {}

    if request.method == 'POST':

        # 1. get otp from text box
        # 2. validate from session table
        try:
            session = Session.objects.get(session_id=request.POST.getlist('OTP')[0].strip())
        except:
            context['error'] = 'The OTP you have entered is invalid'
            return render(request, template, context)

        # 3. validate attendance
        if questions_view.attendance_from_session(session) >= questions_view.attendance_from_attendance(session):
            context['error'] = "Sorry, the attendance limit has been reached."
            return render(request, template, context)

        # 4. Start a django session and redirect to the feedback questions page
        request.session['sessionObj'] = session.session_id
        request.session['classId'] = str(session.initiation_id.class_id)
        request.session['next_feedback'] = session.initiation_id.feedback_of
        return view_helper.get_next_fdbk_response(request)

    return render(request, template, context)
