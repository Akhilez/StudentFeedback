from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMessage

from StudentFeedback.settings import LOGIN_URL

from feedback.forms import *
from feedback.libs.view_helper import *
from feedback.libs.view_helpers.login_helper import *
from feedback.libs.view_helpers.conduct_helper import *
from feedback.libs.view_helpers.initiate_helper import *


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
        return goto_max_page(request)

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
        return goto_max_page(request)

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
def conduct(request, editable):
    if feedback_running(request):
        return goto_max_page(request)

    if not_conductor(request):
        return invalid_user_page(request)

    context = {'active': 'home'}
    template = 'feedback/conduct.html'

    # if his session is selected to edit:
    if editable != '':
        return get_editable_result(request, template, context, editable)

    add_classes_for_session_selection(context)

    if request.method == 'POST':

        if 'confirmSession' in request.POST:
            return confirm_session_result(request, template, context)

        if 'take_attendance' in request.POST:
            return take_attendance_result(request, template, context)

        if 'disableStuLogin' in request.POST:
            disable_student_login(context['otp'], context)

        if 'enableStuLogin' in request.POST:
            enable_student_login(context['otp'], context)

    return render(request, template, context)


@login_required()
def latelogin(request, session_id):
    context = {}
    template = 'feedback/latelogin.html'

    # get the session from session_id url
    session = get_object_or_404(Session, session_id=session_id)
    if get_cur_time_offset(session) > get_session_length():
        raise Http404

    context['session'] = session
    presentClass = session.initiation_id.class_id

    # get all the students
    allStudents = Student.objects.filter(class_id=presentClass)
    presentStudents = Attendance.objects.filter(session_id=session)
    presentStudents = [x for x in presentStudents]
    if session.mastersession is not None:
        more_students = Attendance.objects.filter(session_id=get_master_session(session))
        for att in more_students:
            presentStudents.append(att)
    slav = get_slave(session)
    if slav is not None:
        more_students = Attendance.objects.filter(session_id=slav)
        for att in more_students:
            presentStudents.append(att)
    presentStudents = [student.student_id for student in presentStudents]
    absentStudents = []
    for student in allStudents:
        if student not in presentStudents:
            absentStudents.append(student)

    context['students'] = absentStudents

    if request.method == 'POST':
        attendance = request.POST.getlist('attendance')
        for stud in attendance:
            Attendance.objects.create(student_id=Student.objects.get(hallticket_no=stud), session_id=session)

        cur_time = get_cur_time_offset(session)
        if cur_time > int(session.stutimeout) - getGracePeriod():
            tempTime = cur_time + getGracePeriod()
            session.stutimeout = tempTime
            session.save()

        return redirect('/feedback/conduct')

    return render(request, template, context)


def student(request):
    if request.session.get('sessionObj') is not None:
        maxPage = request.session.get('maxPage', [1, 'faculty'])
        return goto_questions_page(maxPage[0], maxPage[1])

    template = 'feedback/student_login.html'
    context = {}
    # Are any sessions open?
    sessions = Session.objects.all().order_by('-timestamp')[:50]

    # get max stutimeout
    max_timeout = 0
    for session in sessions:
        if session.stutimeout > max_timeout:
            max_timeout = session.stutimeout

    # disable page condition:
    if len(sessions) == 0 or (
                datetime.datetime.now(datetime.timezone.utc) - sessions[
                0].timestamp).total_seconds() / 60 - 30 > max_timeout:
        context['disabled'] = True

    if request.method == 'POST':
        otpFromBox = request.POST.getlist('OTP')[0]
        classObj = None
        for session in sessions:
            if str(session.session_id) == otpFromBox:
                # check if session is open
                if (datetime.datetime.now(
                        datetime.timezone.utc) - session.timestamp).total_seconds() / 60 - 30 > session.stutimeout:
                    context['error'] = "Feedback session expired, please contact your lab in-charge"
                    return render(request, template, context)

                # check the attendance
                attendance = Attendance.objects.filter(session_id=session).count()
                attendanceCount = Feedback.objects.filter(session_id=session).values_list(
                    'student_no').distinct().count()
                if session.mastersession is not None:
                    attendance += Attendance.objects.filter(session_id=get_master_session(session)).count()
                    attendanceCount += Feedback.objects.filter(
                        session_id=get_master_session(session)).values_list(
                        'student_no').distinct().count()
                context['attendance'] = str(attendance) + ' ' + str(attendanceCount)
                if attendanceCount >= attendance:
                    context['error'] = "Sorry, the attendance limit has been reached."
                    return render(request, template, context)

                # Start a django session and redirect to the feedback questions page
                request.session['sessionObj'] = session.session_id
                request.session['classId'] = session.initiation_id.class_id.__str__()
                return redirect('/feedback/questions')
        if classObj is None:
            context['error'] = 'The OTP you have entered is invalid'
    return render(request, template, context)


def questions(request, category):
    session_id = request.session.get('sessionObj')
    if session_id is None:
        return redirect('/')

    maxPage = request.session.get('maxPage')
    if maxPage is None:
        maxPage = [1, 'faculty']
        request.session['maxPage'] = maxPage

    template = 'feedback/questions.html'
    context = {}

    session = Session.objects.get(session_id=session_id)

    attendance = Attendance.objects.filter(session_id=session).count()
    attendanceCount = Feedback.objects.filter(session_id=session).values_list('student_no').distinct().count()
    context['attendance'] = str(attendance) + ' ' + str(attendanceCount)
    if attendanceCount > attendance:
        del request.session['sessionObj']
        return HttpResponse("Sorry, the attendance limit has been reached.")

    # GET CATEGORY
    if category == '': category = 'faculty'
    try:
        category = Category.objects.get(category=category)
    except:
        del request.session['sessionObj']
        return HttpResponse("Thank you for the feedback. There is an error, please call your lab coordinator")
    context['category'] = category.category


    # GET CLASS OBJECT
    classObj = session.initiation_id.class_id
    context['class_obj'] = classObj

    # GET ALL THE CONTENT DETAILS - CLASSES, CFS, ETC
    paging = [0]
    subjects = []
    faculty = []
    cfsList = []
    if category.category == 'faculty':
        cfs = ClassFacSub.objects.filter(class_id=classObj)
        for i in cfs:
            cfsList.append(i)
            subjects.append(i.subject_id.name)
            faculty.append(i.faculty_id)
            context['subjects'] = subjects
        paging = subjects
    paginator = Paginator(paging, 1)

    # GET THE PAGE INFORMATION
    page = request.GET.get('page')
    try:
        pager = paginator.page(page)
    except PageNotAnInteger:
        pager = paginator.page(1)
    except EmptyPage:
        pager = paginator.page(paginator.num_pages)
    context['pager'] = pager
    pgno = str(pager.number)

    # CHECK IF WE ARE ON THE RIGHT PAGE NUMBER
    if pager.number != maxPage[0]:
        return redirect('/feedback/questions/' + maxPage[1] + '/?page=' + str(maxPage[0]))

    if category.category == 'faculty':
        context['subject'] = subjects[pager.number - 1]
        context['faculty'] = faculty[pager.number - 1]

    questionsList = []
    subCategsList = []
    questionsQList = FdbkQuestions.objects.filter(category=category)

    for i in questionsQList:
        questionsList.append(i)
    context['questions'] = questionsList
    currentSubCategory = ''
    subcategoryOrder = []
    for i in range(len(questionsList)):
        if questionsList[i].subcategory != currentSubCategory and questionsList[i].subcategory is not None:
            currentSubCategory = questionsList[i].subcategory
            subcategoryOrder.append(i + 1)
    context['subcategory'] = subcategoryOrder

    myRating = request.session.get(pgno, None)
    if myRating is not None:
        context['allRatings'] = request.session[pgno]
    else:
        request.session[pgno] = None

    if request.method == 'POST':
        try:
            ratings = []
            for i in range(1, len(questionsList) + 1):
                name = 'star' + str(i)
                value = request.POST[name]
                ratings.append(value)
            request.session[pgno] = ratings
            max = request.session.get('maxPage', [1, 'faculty'])
            max[0] += 1
            request.session['maxPage'] = max
        except MultiValueDictKeyError:
            context['error'] = "Please enter all the ratings"
            return render(request, template, context)

        if 'next' in request.POST:
            #return render(request, template, context)
            return redirect('/feedback/questions/' + category.category + '/?page=' + str(pager.number + 1))

        if 'finish' in request.POST:
            del request.session['maxPage']
            student_no = Feedback.objects.filter(session_id=session, category=category)
            if len(student_no) == 0:
                student_no = 1
            else:
                student_no = student_no.order_by('-student_no')[0].student_no + 1

            #GET THE REMARKS FROM HTML
            remarks = request.POST.getlist('remarks')
            if remarks is not None and len(remarks) == 1 and remarks[0] != '':
                remarks = Notes.objects.create(note=remarks[0], session_id=session)

            if category.category == 'faculty':
                for i in range(1, pager.end_index() + 1):
                    if request.session.get(str(i)) is None or None in request.session[str(i)]:
                        return redirect('/feedback/questions/?page=' + str(i))

                for i in range(0, len(cfsList)):
                    ratingsString = ""
                    for j in range(0, len(questionsList)):
                        ratingsString += str(request.session[str(i + 1)][j])
                        if j != len(questionsList) - 1:
                            ratingsString += ","
                    Feedback.objects.create(session_id=session, category=category,
                                            relation_id=str(cfsList[i].cfs_id), student_no=student_no,
                                            ratings=ratingsString)

                # Setting up the classs_id cookie for facility feedback
                class_id_for_cookie = str(session.initiation_id.class_id.class_id)
                request.session['class_id'] = class_id_for_cookie
                response = HttpResponse('blah')
                response.set_cookie('class_id2', class_id_for_cookie)


                # Deleting all the session variables
                #del request.session['sessionObj']
                #for key in list(request.session.keys()):
                #    del request.session[key]


                #TODO store macaddress so that this PC is not used again with the session id
                #return HttpResponse("Thank you for the most valuable review!")
                #return redirect('http://facility.feedback.com/')#('/feedback/questions/facility')
                return redirect('/feedback/LoaQuestions')

            if category.category == 'facility':
                ratingsString = ""
                for i in range(0, len(ratings)):
                    ratingsString += str(ratings[i])
                    if i != len(ratings) - 1:
                        ratingsString += ","
                Feedback.objects.create(session_id=session, category=category, student_no=student_no,
                                        ratings=ratingsString)
                del request.session['sessionObj']
                return HttpResponse("Thank you for the most valuable review!")
                #return redirect('/feedback/questions/LOA')

    return render(request, template, context)


@login_required
def mysessions(request):
    template = "feedback/mysessions.html"
    context = {'active': 'mysessions'}

    # get all sessions started by the user
    allSessions = Session.objects.filter(taken_by=request.user).order_by('-timestamp')[:50]

    running_sessions = []

    for session in allSessions:
        cur_time = get_cur_time_offset(session)
        if session.timestamp.date() == datetime.date.today() and get_session_length() > cur_time:
            running_sessions.append(session.session_id)

    context['allSessions'] = allSessions
    context['running'] = running_sessions

    return render(request, template, context)


@login_required
def changepass(request):
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
    session_id = request.session.get('sessionObj')
    if session_id is None:
        return redirect('/')

    maxPage = request.session.get('maxPage')
    if maxPage is None:
        maxPage = [1, 'LOA']
        request.session['maxPage'] = maxPage

    template = 'feedback/loaquestions.html'
    context = {}

    session = Session.objects.get(session_id=session_id)

    attendance = Attendance.objects.filter(session_id=session).count()
    attendanceCount = FeedbackLoa.objects.filter(session_id=session).values_list('student_no').distinct().count()
    context['attendance'] = str(attendance) + ' ' + str(attendanceCount)
    if attendanceCount > attendance:
        del request.session['sessionObj']
        return HttpResponse("Sorry, the attendance limit has been reached.")

    classObj = session.initiation_id.class_id
    context['class_obj'] = classObj
    # paging = [0]
    subjects = []

    cfsList = []

    cfs = ClassFacSub.objects.filter(class_id=classObj)
    for i in cfs:
        cfsList.append(i)
        con = LOAquestions.objects.filter(subject_id=i.subject_id)
        if len(con) > 0:
            subjects.append(i.subject_id)
    context['subjects'] = subjects
    paging = subjects

    paginator = Paginator(subjects, 1)
    page = request.GET.get('page')
    try:
        pager = paginator.page(page)
    except PageNotAnInteger:
        pager = paginator.page(1)
    except EmptyPage:
        pager = paginator.page(paginator.num_pages)
    context['pager'] = pager
    pgno = str(pager.number)

    # CHECK IF WE ARE ON THE RIGHT PAGE NUMBER
    if pager.number != maxPage[0]:
        return redirect('/feedback/questions/' + 'LoaQuestions' + '/?page=' + str(maxPage[0]))

    context['current'] = subjects[pager.number - 1]
    mysubid = subjects[pager.number - 1]
    # return HttpResponse(mysubid)
    myques = LOAquestions.objects.filter(subject_id=mysubid)
    loaquestions = []
    for q in myques:
        loaquestions.append(q.question)
    context['learningquestions'] = loaquestions

    context['akhilrat'] = request.session.get(pgno)
    if request.method == 'POST':
        try:
            ratings = []

            for i in range(1, len(loaquestions) + 1):
                name = 'star' + str(i)
                value = request.POST[name]
                ratings.append(value)

            request.session[pgno] = ratings
            context['currat'] = ratings
            max = request.session.get('maxPage', [1, 'LOA'])
            max[0] += 1
            request.session['maxPage'] = max

        except MultiValueDictKeyError:
            context['error'] = "Please enter all the ratings"
            return render(request, template, context)

        if 'next' in request.POST:
            return redirect('/feedback/LoaQuestions/?page=' + str(pager.number + 1))

        if 'submit' in request.POST:
            student_no = FeedbackLoa.objects.filter(session_id=session)

            if len(student_no) == 0:
                student_no = 1
            else:
                student_no = student_no.order_by('-student_no')[0].student_no + 1

            for i in range(len(subjects)):
                loaratings = ""
                temp = []
                temp = request.session.get(str(i + 1))
                for k in range(len(temp)):
                    loaratings += temp[k]
                    if k != len(temp) - 1:
                        loaratings += ','
                FeedbackLoa.objects.create(session_id=session, student_no=student_no,
                                           relation_id=subjects[i].subject_id, loaratings=loaratings)

            del request.session['sessionObj']
            del request.session['maxPage']
            response = redirect('http://10.11.46.162/')
            response.set_cookie('class_id', session.initiation_id.class_id.class_id)
            return response

    return render(request, template, context)


def updatedb(request):
    template = 'feedback/updatedb.html'
    context = {}
    data = None

    # data = db_updater.update_classes()
    # data = db_updater.update_students()
    # data = db_updater.update_faculty()
    #data = db_updater.update_subjects()
    #data = db_updater.update_class_fac_sub()
    #data = db_updater.update_faculty_questions()
    data = db_updater.update_loa_questions()

    context['classes'] = data

    return render(request, template, context)


def forgotPassword(request):
    template = 'feedback/forgotPassword.html/'
    email = EmailMessage('hii', 'hiiiiii', to=['rajrocksdeworld@gmail.com'])
    email.send()
    return render(request, template, {})




