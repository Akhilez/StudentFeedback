from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMessage

from StudentFeedback.settings import LOGIN_URL, ALLOWED_HOSTS
from analytics.libs import db_updater
from feedback.forms import *
from feedback.libs.view_helper import *
from feedback.libs.view_helpers.login_helper import *
from feedback.libs.view_helpers.conduct_helper import *
from feedback.libs.view_helpers.initiate_helper import *
from feedback.libs import log


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

    return render(request, template, context)


@login_required()
def latelogin(request, session_id):
    if feedback_running(request):
        return redirect('/feedback/questions/')

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
    if feedback_running(request):
        return redirect('/feedback/questions/')

    template = 'feedback/student_login.html'
    context = {}
    # Are any sessions open?
    sessions = Session.objects.all().order_by('-timestamp')[:50]

    if request.method == 'POST':
        otpFromBox = request.POST.getlist('OTP')[0].strip()
        classObj = None
        for session in sessions:
            if str(session.session_id) == otpFromBox:

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


def questions(request):
    session_id = request.session.get('sessionObj')
    if session_id is None:
        return redirect('/')

    template = 'feedback/questions.html'
    context = {}

    session = Session.objects.get(session_id=session_id)

    attendance = Attendance.objects.filter(session_id=session).count()
    attendanceCount = Feedback.objects.filter(session_id=session).values_list('student_no').distinct().count()
    if attendanceCount > attendance:
        del request.session['sessionObj']
        return HttpResponse("Sorry, the attendance limit has been reached.")

    # GET CATEGORY
    category = Category.objects.get(category='faculty')

    # GET CLASS OBJECT
    classObj = session.initiation_id.class_id
    context['class_obj'] = classObj

    # GET ALL THE CONTENT DETAILS - CLASSES, CFS, ETC
    cfsList = []
    for cfs in ClassFacSub.objects.filter(class_id=classObj):
        if not re.compile("^.* [Ll][Aa][Bb]$").match(cfs.subject_id.name) and not re.compile(
                "[Mm][eE][nN][tT][oO][rR][iI][nN][gG]").match(cfs.subject_id.name):
            cfsList.append(cfs)

    context['cfs_list'] = cfsList

    questionsList = [ques for ques in FdbkQuestions.objects.filter(category=category)]
    context['questions'] = questionsList

    currentSubCategory = ''
    subcategoryOrder = []
    for i in range(len(questionsList)):
        if questionsList[i].subcategory != currentSubCategory and questionsList[i].subcategory is not None:
            currentSubCategory = questionsList[i].subcategory
            subcategoryOrder.append(i + 1)
    context['subcategory'] = subcategoryOrder

    if request.method == 'POST':
        if 'finish' in request.POST:
            student_no = Feedback.objects.filter(session_id=session, category=category)
            if len(student_no) == 0:
                student_no = 1
            else:
                student_no = student_no.order_by('-student_no')[0].student_no + 1

            # GET THE REMARKS FROM HTML
            remarks = request.POST.getlist('remarks')
            if remarks is not None and len(remarks) == 1 and remarks[0] != '':
                Notes.objects.create(note=remarks[0], session_id=session)

            for i in range(0, len(cfsList)):
                ratingsString = ""
                for j in range(0, len(questionsList)):
                    ratingsString += str(
                        request.POST['star-' + str(questionsList[j].question_id) + '-' + str(cfsList[i].cfs_id)])
                    if j != len(questionsList) - 1:
                        ratingsString += ","
                Feedback.objects.create(session_id=session, category=category,
                                        relation_id=str(cfsList[i].cfs_id), student_no=student_no,
                                        ratings=ratingsString)

            # return HttpResponse("Thank you for the most valuable review!")
            #return redirect('http://facility.feedback.com/')#('/feedback/questions/facility')
            return redirect('/feedback/LoaQuestions')

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
        #con = LOAquestions.objects.filter(subject_id=i.subject_id)
        #if len(con) > 0:
        subjects.append(i.subject_id)
    context['subjects'] = subjects

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
        return redirect('/feedback/LoaQuestions/?page=' + str(maxPage[0]))

    log.write(str(pager.number))

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
                temp = request.session.get(str(i + 1))
                for k in range(len(temp)):
                    loaratings += temp[k]
                    if k != len(temp) - 1:
                        loaratings += ','
                FeedbackLoa.objects.create(session_id=session, student_no=student_no,
                                           relation_id=subjects[i].subject_id, loaratings=loaratings)

            del request.session['sessionObj']
            del request.session['maxPage']
            response = redirect('http://'+str(ALLOWED_HOSTS[len(ALLOWED_HOSTS)-1])+'/')
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
    # data = db_updater.update_subjects()
    # data = db_updater.update_class_fac_sub()
    #data = db_updater.update_faculty_questions()
    data = db_updater.update_loa_questions()

    context['classes'] = data

    return render(request, template, context)


def forgotPassword(request):
    template = 'feedback/forgotPassword.html/'
    email = EmailMessage('hii', 'hiiiiii', to=['rajrocksdeworld@gmail.com'])
    email.send()
    return render(request, template, {})




