from django.contrib.auth.decorators import login_required

from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMessage

from StudentFeedback.settings import LOGIN_URL
from analytics.libs import db_updater

from feedback.forms import *
from feedback.libs.config_helper import get_max_subjects_each_page_loa, get_max_cfs_each
from feedback.libs.view_helper import *
from feedback.libs.view_helpers.login_helper import *
from feedback.libs.view_helpers.conduct_helper import *
from feedback.libs.view_helpers.initiate_helper import *
from feedback.libs.view_helpers import loa_helper
from feedback.libs.view_helpers import questions_helper


def login_redirect(request):
    # if any user already logged in, take to their homepage
    if request.user.is_authenticated():
        return goto_user_page(request.user)

    # is any initiation open? then go to student otp page.
    if len(get_todays_initiations()) > 0:
        return redirect('/feedback/student')

    return redirect(LOGIN_URL)


def login_view(request):
    if feedback_running(request):
        return redirect('/feedback/questions/')

    if request.user.is_authenticated:
        return goto_user_page(request.user)

    template = "login.html"
    context = {}

    if request.method == "POST":
        if 'login' in request.POST:
            return login_result(request, template, context)
    else:
        context['form'] = LoginForm()

    return render(request, template, context)


@login_required
def initiate(request):
    if feedback_running(request):
        return redirect('/feedback/questions/')

    if not_coordinator(request):
        return invalid_user_page(request)

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


@login_required
def conduct(request):
    if feedback_running(request):
        return redirect('/feedback/questions/')

    if not_conductor(request):
        return invalid_user_page(request)

    context = {'active': 'home'}
    template = 'feedback/conduct.html'

    add_my_sessions(request.user, context)
    add_classes_for_session_selection(context)

    if request.method == 'POST':

        if 'confirmSession' in request.POST:
            return confirm_session_result(request)

        if 'take_attendance' in request.POST:
            return take_attendance_result(request, template, context)

        if 'makemaster' in request.POST:
            return make_master_result(request.POST['makemaster'])

    return render(request, template, context)


@login_required()
def latelogin(request, session_id):
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
    context['students'] = get_absent_students_for_late_login(session)

    return render(request, template, context)


def student(request):
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
        otpFromBox = request.POST.getlist('OTP')[0].strip()

        # 2. validate from session table
        try:
            session = Session.objects.get(session_id=otpFromBox)
        except:
            context['error'] = 'The OTP you have entered is invalid'
            return render(request, template, context)

        # 3. validate attendance
        if questions_helper.attendance_from_session(session) >= questions_helper.attendance_from_attendance(session):
            context['error'] = "Sorry, the attendance limit has been reached."
            return render(request, template, context)

        # 4. Start a django session and redirect to the feedback questions page
        request.session['sessionObj'] = session.session_id
        request.session['classId'] = str(session.initiation_id.class_id)
        return redirect('/feedback/questions')

    return render(request, template, context)


def questions(request):
    """
    1. get session from http session variables
    2. validate attendance
    2.1 make pagination
    2.2 get maxPage if exists else create maxPage
    2.3 get pager indices
    2.4 get cfs for current page
    3. add cfs list of the page to context, ignore labs and mentoring
    4. add questions-set to context
    5. add sub-category order to context
    6. Handle finish button
    :param request:
    :return: http response
    """
    session_id = request.session.get('sessionObj')
    if session_id is None:
        return redirect('/')

    template = 'feedback/questions.html'
    context = {}

    # 1. get session from http session variables
    session = Session.objects.get(session_id=session_id)

    # 2. validate attendance
    if questions_helper.attendance_from_session(session) >= questions_helper.attendance_from_attendance(session):
        del request.session['sessionObj']
        return HttpResponse("Sorry, the attendance limit has been reached.")

    # get necessary details
    all_cfs_list = questions_helper.get_cfs_for(class_id=session.initiation_id.class_id)
    max_cfs_each = get_max_cfs_each()

    # 2.1 make pagination
    pager = loa_helper.get_pager(request, all_cfs_list, max_cfs_each)
    context['pager'] = pager

    # 2.2 get maxPage if exists else create maxPage
    if questions_helper.set_max_page(request, pager.number):
        return redirect('/feedback/questions/?page=' + str(request.session['maxPage'][0]))

    # 2.3 get pager indices
    context['page_index_list'] = [i for i in range(1, max_cfs_each + 1)]

    # 2.4 get cfs for current page
    cfs_list = all_cfs_list[((pager.number - 1) * max_cfs_each): (pager.number * max_cfs_each)]

    # 3. add cfs list to context, ignore labs and mentoring
    context['cfs_list'] = cfs_list
    context['class_obj'] = session.initiation_id.class_id

    # 4. add questions-set to context
    questions_list = [ques for ques in FdbkQuestions.objects.filter(enabled=True)]
    context['questions'] = questions_list

    # 5. add sub-category order to context
    context['subcategory'] = questions_helper.get_subcategory_order(questions_list)

    # 6. Handle finish button:
    if request.method == 'POST':
        if 'next' in request.POST:
            return questions_helper.get_next_result(request, cfs_list, questions_list, pager)

        if 'finish' in request.POST:
            return questions_helper.get_finish_result(request, cfs_list, questions_list, session, all_cfs_list)

    return render(request, template, context)


@login_required
def changepass(request):
    if feedback_running(request):
        return redirect('/feedback/questions/')

    template = 'feedback/changepass.html'
    context = {'conductor_group': CONDUCTOR_GROUP, 'active': 'changepass'}
    if request.method == "POST":
        formset = ProfileForm(request.POST)
        if (formset.is_valid()):
            # formset.save()
            firstname = request.POST.get('firstname', '')
            lastname = request.POST.get('lastname', '')
            newpass = request.POST.get('newpass', '')
            repass = request.POST.get('repass', '')
            email = request.POST.get('email', '')
            password = request.POST.get('password', '')
            if check_password(password, request.user.password):
                if firstname:
                    u = User.objects.get(username=request.user)
                    u.first_name = firstname
                    u.save()
                    context['fir'] = 'notnull'
                if lastname:
                    u = User.objects.get(username=request.user)
                    u.last_name = lastname
                    u.save()
                    context['sec'] = 'notnull'
                if email:
                    u = User.objects.get(username=request.user)
                    u.email = email
                    u.save()
                    context['ec'] = 'notnull'
                if newpass:
                    if repass:
                        if newpass == repass:
                            x = True
                            while x:
                                if (len(newpass) < 6 or len(newpass) > 12):
                                    break
                                elif not re.search("[a-z]", newpass):
                                    break
                                elif not re.search("[0-9]", newpass):
                                    break
                                elif not re.search("[A-Z]", newpass):
                                    break
                                elif re.search("\s", newpass):
                                    break
                                else:
                                    user = request.user
                                    user.set_password(newpass)
                                    user.save()
                                    context['pas'] = 'notnull'
                                    x = False
                                    break
                            if x:
                                context['passnotvalid'] = 'notnull'
                        else:
                            context['repass'] = 'notnull'
            else:
                context['wrongpass'] = 'notnull'
    formset = ProfileForm()
    context['formset'] = formset
    return render(request, template, context)


def LoaQuestions(request):
    """
    1. get session obj or go to /
    2. make pagination
    3. get maxPage if exists else create maxPage
    4. get the subjects for current page
    5. for each subject obj, get its questions, make a SubQues object and pass it to context
    6. handle next button click
    7. handle submit button click
    :param request:
    :return:
    """
    # 1. get session obj or go to /
    session_id = request.session.get('sessionObj')
    if session_id is None:
        return redirect('/')

    template = 'feedback/loaquestions.html'
    context = {}

    # get all the necessary details
    session = Session.objects.get(session_id=session_id)
    class_obj = session.initiation_id.class_id
    context['class_obj'] = class_obj
    all_subjects = loa_helper.get_all_subjects(class_obj)
    max_sub_each = get_max_subjects_each_page_loa()

    # 2. make pagination
    pager = loa_helper.get_pager(request, all_subjects, max_sub_each)
    context['pager'] = pager

    # 3. get maxPage if exists else create maxPage
    if loa_helper.set_max_page(request, pager.number):
        return redirect('/feedback/LoaQuestions/?page=' + str(request.session['maxPage'][0]))

    # get the pager indices
    context['page_index_list'] = [i for i in range(1, max_sub_each + 1)]

    # 4. get the subjects for current page
    subjects = all_subjects[((pager.number - 1) * max_sub_each): (pager.number * max_sub_each)]

    # 5. for each subject obj, get its questions, make a SubQues object and pass it to context
    sub_ques_list = loa_helper.get_sub_ques_list(subjects)
    context['sub_ques_list'] = sub_ques_list

    if request.method == 'POST':
        # 6. handle next button click
        if 'next' in request.POST:
            return loa_helper.next_button_result(request, template, context)

        # 7. handle submit button click
        if 'submit' in request.POST:
            return loa_helper.submit_button_result(request, context, session, all_subjects)

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

    context['classes'] = data

    return render(request, template, context)


def forgotPassword(request):
    template = 'feedback/forgotPassword.html/'
    email = EmailMessage('hii', 'hiiiiii', to=['rajrocksdeworld@gmail.com'])
    email.send()
    return render(request, template, {})
