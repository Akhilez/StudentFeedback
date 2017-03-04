from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from StudentFeedback.settings import COORDINATOR_GROUP, CONDUCTOR_GROUP, LOGIN_URL, DIRECTOR_GROUP
from feedback.forms import *
from django.contrib.auth.decorators import login_required
from feedback.models import *
import random
import string
from django.contrib.auth.hashers import check_password
from django.core.signing import *
import re


def get_todays_initiations():
    all_initiations = Initiation.objects.all()
    initiations_list = []
    for initiation in all_initiations:
        if initiation.timestamp.date() == datetime.date.today():
            initiations_list.append(initiation)
    return initiations_list


def get_session_length():
    return 45


def login_redirect(request):
    if request.user.is_authenticated():
        return redirect(LOGIN_URL)
    # is any initiation open? then go to student otp page.
    if len(get_todays_initiations()) > 0:
        return redirect('/feedback/student')
    return redirect(LOGIN_URL)


def login_view(request):
    if request.session.get('sessionObj') is not None:
        maxPage = request.session.get('maxPage', [1, 'faculty'])
        return goto_questions_page(maxPage[0], maxPage[1])

    if request.user.is_authenticated:
        return goto_user_page(request.user)
    template = "login.html"
    context = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return goto_user_page(user)
            else:
                context['error'] = 'login error'
            context['form'] = form
    else:
        context['form'] = LoginForm()
    return render(request, template, context)


def goto_user_page(user):
    if user.groups.filter(name=COORDINATOR_GROUP).exists():
        return redirect('/feedback/initiate/')
    elif user.groups.filter(name=CONDUCTOR_GROUP).exists():
        return redirect('/feedback/conduct/')
    elif user.groups.filter(name=DIRECTOR_GROUP).exists():
        return redirect('/analytics/')
    elif user.is_superuser:
        return redirect('/admin/')
    return HttpResponse("You are already logged in")


@login_required
def initiate(request):
    if request.session.get('sessionObj') is not None:
        maxPage = request.session.get('maxPage', [1, 'faculty'])
        return goto_questions_page(maxPage[0], maxPage[1])

    groups = request.user.groups.all()
    if not groups.filter(name=COORDINATOR_GROUP).exists():
        return render(request, 'feedback/invalid_user.html')

    context = {'active': 'home'}

    myBranches = []
    for group in groups:
        if group.name != COORDINATOR_GROUP:
            myBranches.append(group.name)

    context['groups'] = myBranches

    context['total_history'] = Initiation.objects.all().order_by('-timestamp')[:10]
    template = 'feedback/initiate.html'

    context['recent_feedbacks'] = Session.objects.all().order_by('-timestamp')[:10]

    years = Classes.objects.order_by('year').values_list('year').distinct()  # returns a list of tuples
    years = [years[x][0] for x in range(len(years))]  # makes a list of first element of tuples in years
    context['years'] = years
    context['allYears'] = years

    # handling the submit buttons
    if request.method == 'POST':

        if 'nextSection' in request.POST:
            allClasses = Classes.objects.all().order_by('year')
            notEligible = []

            selectedYears = request.POST.getlist('class')
            classesOfYears = []
            for yr in selectedYears:
                myYear = allClasses.filter(year=yr)
                for myYr in myYear:
                    for myBranch in myBranches:
                        if myYr.branch == myBranch:
                            classesOfYears.append(myYr)
                            break
            context['myClasses'] = classesOfYears

            for i in range(len(classesOfYears)):
                if isNotEligible(classesOfYears[i]):
                    notEligible.append(i + 1)
            context['notEligible'] = notEligible

        if 'confirmSelected' in request.POST:
            checkedList = request.POST.getlist('class')
            lst = []
            for i in checkedList:
                inst = i.split('-')
                status = initiateFor(inst[0], inst[1], inst[2], request.user)
                lst.append(inst[0] + inst[1] + inst[2] + " - " + status)
            context['status'] = lst

    return render(request, template, context)


def get_cur_time_offset(session):
    return int((datetime.datetime.now(datetime.timezone.utc) - session.timestamp).total_seconds() / 60)


@login_required
def conduct(request, editable):
    if request.session.get('sessionObj') is not None:
        maxPage = request.session.get('maxPage', [1, 'faculty'])
        return goto_questions_page(maxPage[0], maxPage[1])

    if not request.user.groups.filter(name=CONDUCTOR_GROUP).exists():
        return render(request, 'feedback/invalid_user.html')

    context = {'active': 'home'}
    template = 'feedback/conduct.html'

    if editable != '':
        session = get_object_or_404(Session, session_id=editable)
        if get_cur_time_offset(session) > get_session_length():
            raise Http404
        context['otp'] = editable
        context['classSelected'] = session.initiation_id.class_id

        cur_time = get_cur_time_offset(session)
        if session.stutimeout > cur_time:
            context['warning'] = "The student login page is enabled!"
        else:
            context['success'] = "Enable the student page"

        if request.method == 'POST':
            if 'disableStuLogin' in request.POST:
                try:
                    session = Session.objects.get(session_id=editable)
                    session.stutimeout = getStudentTimeout()
                    session.save()
                    del context['warning']
                    context['success'] = "Enable the student page"
                except KeyError: pass
            if 'enableStuLogin' in request.POST:
                try:
                    session = Session.objects.get(session_id=editable)
                    session.stutimeout = get_cur_time_offset(session) + getGracePeriod()
                    session.save()
                    del context['success']
                    context['warning'] = "The student login page is enabled!"
                except KeyError:pass

        return render(request, template, context)

    allSessions = Session.objects.all().order_by('-timestamp')


    # GET ALL SESSIONS TO RESTRICT THE INITIATIONS
    sessionsList = []
    for session in allSessions:
        if session.timestamp.date() == datetime.date.today():
            if session.master == False:
                sessionsList.append(session.initiation_id)

    # GET ALL INITIATIONS
    allInits = Initiation.objects.all()
    initlist = []
    for i in allInits:
        if i.timestamp.date() == datetime.date.today():
            if i not in sessionsList:
                initlist.append(i)
    if len(initlist) != 0:
        context['classes'] = initlist

    masterSession = None

    if request.method == 'POST':

        if 'confirmSession' in request.POST:

            #is the session required to split? if yes, the current session is master
            split = request.POST.getlist('master')
            if len(split) > 0:
                master = True
            else:
                master = False

            #get the class from session
            classFromSelect = request.session.get('class')


            #get the attendance
            checkValues = request.POST.getlist("attendanceList")

            #generate otp
            otp = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

            dt = str(datetime.datetime.now())
            alreadyThere = False

            #get the initiation obj from selected class
            initObj = None
            for init in initlist:
                if str(init.class_id.class_id) == str(classFromSelect):
                    initObj = init
                    break
            context['classSelected'] = initObj.class_id

            #check if session exists
            for session0 in allSessions:
                if initObj == session0.initiation_id:
                    masterSession = session0
                    alreadyThere = True
                    break

            #insert new session record
            if not alreadyThere:
                session = Session.objects.create(timestamp=dt, taken_by=request.user, initiation_id=initObj,
                                                       session_id=otp, master=master, stutimeout=getStudentTimeout())
            else:
                masterSession.master = False
                masterSession.save()
                session = Session.objects.create(timestamp=dt, taken_by=request.user, initiation_id=initObj,
                                                 session_id=otp, master=False, mastersession=masterSession.session_id,
                                                 stutimeout=getStudentTimeout())

            #Add disable button
            context['warning'] = "The student login page is enabled!"

            #save the otp in session
            context['otp'] = otp

            #insert the attendance into table
            for htno in checkValues:
                Attendance.objects.create(student_id=Student.objects.get(hallticket_no=htno), session_id=session)

        if 'take_attendance' in request.POST:
            master = False

            # get the class obj from the dropdown
            classFromSelect = request.POST.getlist('selectClass')[0]
            classObj = Classes.objects.get(class_id=classFromSelect)

            # set the context and session with class
            context['classSelected'] = classObj
            request.session['class'] = classObj.class_id

            alreadyThere = False

            # get the initiation object of the selected class
            initObj = None
            for init in initlist:
                if str(init.class_id.class_id) == str(classFromSelect):
                    initObj = init
                    break

            # check if there are any sessions with the initiation id, if yes, is it a master session?
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

        if 'disableStuLogin' in request.POST:
            try:
                session = Session.objects.get(session_id=context['otp'])
                session.stutimeout = getStudentTimeout()
                session.save()
                del context['warning']
                context['success'] = "Enable the student page"

            except KeyError:
                pass

        if 'enableStuLogin' in request.POST:
            try:
                session = Session.objects.get(session_id=context['otp'])
                session.stutimeout = get_cur_time_offset(session) + getGracePeriod()
                session.save()
                del context['success']
                context['warning'] = "The student login page is enabled!"
            except KeyError:
                pass

    return render(request, template, context)


def get_master_session(session):
    if session.mastersession is None:
        return session
    return Session.objects.get(session_id=session.mastersession)


def get_slave(session):
    sessions = Session.objects.all().order_by('-timestamp')[:20]
    for sess in sessions:
        if sess.mastersession == session.session_id:
            return sess
    return None


@login_required()
def latelogin(request, session_id):
    context = {}
    template = 'feedback/latelogin.html'

    #get the session from session_id url
    session = get_object_or_404(Session, session_id=session_id)
    if get_cur_time_offset(session) > get_session_length():
        raise Http404

    context['session'] = session
    presentClass = session.initiation_id.class_id

    #get all the students
    allStudents = Student.objects.filter(class_id=presentClass)
    presentStudents = Attendance.objects.filter(session_id=session)
    presentStudents = [x for x in presentStudents]
    if session.mastersession is not None:
        more_students =  Attendance.objects.filter(session_id=get_master_session(session))
        for att in more_students:
            presentStudents.append(att)
    slav = get_slave(session)
    if slav is not None:
        more_students =  Attendance.objects.filter(session_id=slav)
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
        if cur_time > int(session.stutimeout)-getGracePeriod():
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
    if len(sessions) == 0 or (datetime.datetime.now(datetime.timezone.utc) - sessions[0].timestamp).total_seconds() / 60 > max_timeout:
        context['disabled'] = True


    if request.method == 'POST':
        otpFromBox = request.POST.getlist('OTP')[0]
        classObj = None
        for session in sessions:
            if str(session.session_id) == otpFromBox:
                # check if session is open
                if (datetime.datetime.now(datetime.timezone.utc) - session.timestamp).total_seconds() / 60 > session.stutimeout:
                    context['error'] = "Feedback session expired, please contact your lab in-charge"
                    return render(request, template, context)

                #check the attendance
                attendance = Attendance.objects.filter(session_id=session).count()
                attendanceCount = Feedback.objects.filter(session_id=session).values_list('student_no').distinct().count()
                if session.mastersession is not None:
                    attendance += Attendance.objects.filter(session_id=get_master_session(session)).count()
                    attendanceCount += Feedback.objects.filter(session_id=get_master_session(session)).values_list('student_no').distinct().count()
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
    except :
        del request.session['sessionObj']
        return HttpResponse("Thank you for the feedback. There is an error, please call your lab coordinator")
    context['category'] = category.category


    # GET CLASS OBJECT
    classObj = session.initiation_id.class_id
    context['class_obj'] = classObj

    #GET ALL THE CONTENT DETAILS - CLASSES, CFS, ETC
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

    #GET THE PAGE INFORMATION
    page = request.GET.get('page')
    try:
        pager = paginator.page(page)
    except PageNotAnInteger:
        pager = paginator.page(1)
    except EmptyPage:
        pager = paginator.page(paginator.num_pages)
    context['pager'] = pager
    pgno = str(pager.number)

    #CHECK IF WE ARE ON THE RIGHT PAGE NUMBER
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
                                            relation_id=str(cfsList[i - 1].cfs_id), student_no=student_no,
                                            ratings=ratingsString)

                # Setting up the classs_id cookie for facility feedback
                class_id_for_cookie = str(session.initiation_id.class_id.class_id)
                request.session['class_id'] = class_id_for_cookie
                response = HttpResponse('blah')
                response.set_cookie('class_id2', class_id_for_cookie)


                # Deleting all the session variables
                del request.session['sessionObj']
                #for key in list(request.session.keys()):
                #    del request.session[key]


                #TODO store macaddress so that this PC is not used again with the session id
                #return HttpResponse("Thank you for the most valuable review!")
                return redirect('http://facility.feedback.com/')#('/feedback/questions/facility')

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

    #get all sessions started by the user
    allSessions = Session.objects.filter(taken_by=request.user).order_by('-timestamp')[:50]

    running_sessions = []

    for session in allSessions:
        cur_time = get_cur_time_offset(session)
        if session.timestamp.date() == datetime.date.today() and get_session_length() > cur_time:
            running_sessions.append(session.session_id)

    context['allSessions'] = allSessions
    context['running'] = running_sessions

    return render(request, template, context)


def initiateFor(year, branch, section, by):
    classobj = Classes.objects.get(year=year, branch=branch, section=section)
    history = Initiation.objects.filter(class_id=classobj)
    if len(history) == 0 or history[len(history) - 1].timestamp.date() != datetime.date.today():
        dt = str(datetime.datetime.now())
        Initiation.objects.create(timestamp=dt, initiated_by=by, class_id=classobj)
        return 'success'
    else:
        return 'failed'


def getStudentTimeout():
    try:
        timeInMin = Config.objects.get(key='studentTimeout')
        return int(timeInMin.value)
    except Exception:
        Config.objects.create(key='studentTimeout', value='5',
                              description="Expire the student login page after these many seconds")
        return 5


def goto_questions_page(page_no, category='faculty'):
    if page_no is None:
        return redirect('/feedback/questions/')
    return redirect('/feedback/questions/' + category + '/?page=' + str(page_no))


def isNotEligible(cls):
    initiations = Initiation.objects.all()
    for initiation in initiations:
        if initiation.timestamp.date() == datetime.date.today():
            if cls == initiation.class_id:
                return True

    return False


def getGracePeriod():
    try:
        gp = Config.objects.get(key="gracePeriod")
        return int(gp)
    except :
        return 2

@login_required
def changepass(request):
    template = 'feedback/changepass.html'
    context = {'conductor_group': CONDUCTOR_GROUP, 'active': 'changepass'}
    if request.method == "POST":
        formset=ProfileForm(request.POST)
        if(formset.is_valid()):
            #formset.save()
            firstname = request.POST.get('firstname', '')
            lastname = request.POST.get('lastname', '')
            newpass = request.POST.get('newpass', '')
            repass = request.POST.get('repass', '')
            email = request.POST.get('email', '')
            password = request.POST.get('password', '')
            if check_password(password, request.user.password):
                if firstname:
                    u = User.objects.get(username =request.user)
                    u.first_name = firstname
                    u.save()
                if lastname:
                    u = User.objects.get(username =request.user)
                    u.last_name = lastname
                    u.save()
                if email:
                    u = User.objects.get(username =request.user)
                    u.email = email
                    u.save()
                if newpass:
                    if repass:
                        if newpass==repass:
                            x = True
                            while x:
                                if (len(newpass)<6 or len(newpass)>12):
                                    break
                                elif not re.search("[a-z]",newpass):
                                    break
                                elif not re.search("[0-9]",newpass):
                                    break
                                elif not re.search("[A-Z]",newpass):
                                    break
                                elif re.search("\s",newpass):
                                    break
                                else:
                                    user=request.user
                                    user.set_password(newpass)
                                    user.save()
                                    x=False
                                    break
                            if x:
                                context['passnotvalid'] = 'notnull'
                                formset = ProfileForm()
                                context['formset'] = formset
                                return render(request, template, context)

                        else:
                            context['repass'] = 'notnull'
                            formset = ProfileForm()
                            context['formset'] = formset
                            return render(request, template, context)
            else:
                context['wrongpass'] = 'notnull'
                formset = ProfileForm()
                context['formset'] = formset
                return render(request, template, context)
    else:
        formset = ProfileForm()
        context['formset'] = formset
    formset = ProfileForm()
    context['formset'] = formset
    return render(request, template, context)