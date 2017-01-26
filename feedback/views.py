from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.datastructures import MultiValueDictKeyError
from StudentFeedback.settings import COORDINATOR_GROUP, CONDUCTOR_GROUP, LOGIN_URL
from feedback.forms import *
from django.contrib.auth.decorators import login_required
from feedback.models import *
import datetime
import random
import string


def login_redirect(request):
    #Are any sessions open?
    sessions = Session.objects.all().order_by('-timestamp')[:50]
    if len(sessions) != 0 and (datetime.datetime.now(datetime.timezone.utc) - sessions[0].timestamp).total_seconds()/60 < getStudentTimeout():
        return redirect('/feedback/student')
    return redirect(LOGIN_URL)


def login_view(request):

    if request.session.get('sessionObj') is not None:
        return goto_questions_page(request.session.get('maxPage'))

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
    elif user.is_superuser:
        return redirect('/admin/')
    return HttpResponse("You are already logged in")


@login_required
def initiate(request):

    if request.session.get('sessionObj') is not None:
        return goto_questions_page(request.session.get('maxPage'))

    groups = request.user.groups.all()
    if not groups.filter(name=COORDINATOR_GROUP).exists():
        return render(request, 'feedback/invalid_user.html')

    context = {}

    myBranches = []
    for group in groups:
        if group.name != COORDINATOR_GROUP:
            myBranches.append(group.name)

    context['groups'] = myBranches

    #Running Sessions(Today)
    allSessions = Session.objects.all()
    session_lst = []
    for i in allSessions:
        if i.timestamp.date() == datetime.date.today():
            session_lst.append(i)

    context['total_history'] = Initiation.objects.all().order_by('-timestamp')[:10]
    context['running_sessions'] = session_lst
    template = 'feedback/initiate.html'

    context['recent_feedbacks'] = Session.objects.all().order_by('-timestamp')[:10]

    years = Classes.objects.order_by('year').values_list('year').distinct()  # returns a list of tuples
    years = [years[x][0] for x in range(len(years))]  # makes a list of first element of tuples in years
    context['years'] = years
    context['allYears'] = years

    #handling the submit buttons
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
                    notEligible.append(i+1)
            context['notEligible'] = notEligible


        if 'confirmSelected' in request.POST:
            checkedList = request.POST.getlist('class')
            lst = []
            for i in checkedList:
                inst = i.split('-')
                status = initiateFor(inst[0], inst[1], inst[2], request.user)
                lst.append(inst[0]+inst[1]+inst[2]+" - "+status)
            context['status'] = lst



    return render(request, template, context)


@login_required
def conduct(request):

    if request.session.get('sessionObj') is not None:
        return goto_questions_page(request.session.get('maxPage'))

    if not request.user.groups.filter(name=CONDUCTOR_GROUP).exists():
        return render(request, 'feedback/invalid_user.html')

    context = {}
    template = 'feedback/conduct.html'
    hasOtp = request.session.get('otp', None)
    if hasOtp is not None:
        context['otp'] = hasOtp
        context['classSelected'] = Classes.objects.get(class_id=request.session.get('class', None))
        return render(request, template, context)


    #GET ALL SESSIONS TO RESTRICT THE INITIATIONS
    allSessions = Session.objects.all()
    sessionsList = []
    for session in allSessions:
        if session.timestamp.date() == datetime.date.today():
            if session.master == False:
                sessionsList.append(session.initiation_id)

    #GET ALL INITIATIONS
    allInits = Initiation.objects.all()
    initlist = []
    for i in allInits:
        if i.timestamp.date() == datetime.date.today():
            if i not in sessionsList:
                initlist.append(i)
    if len(initlist) != 0:
        context['classes'] = initlist

    if request.method == 'POST' :
        #TODO Session id must be same if already exists
        if 'confirmSession' in request.POST:
            split = request.POST.getlist('master')
            if len(split) > 0:
                master = True
            else: master = False
            classFromSelect = request.session.get('class')
            checkValues = request.POST.getlist("attendanceList")
            otp = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
            dt = str(datetime.datetime.now())
            initObj = None
            for init in initlist:
                if str(init.class_id.class_id) == str(classFromSelect):
                    initObj=init
                    break

            session = None
            alreadyThere = False
            for session0 in allSessions:
                if initObj == session0.initiation_id:
                    session = session0
                    otp = session0.session_id
                    alreadyThere = True
                    break

            context['classSelected'] = initObj.class_id
            if not alreadyThere:
                otp = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
                session = Session.objects.create(timestamp=dt, taken_by=request.user, initiation_id=initObj, session_id=otp, master=master)
            else:
                session.master = False
                session.save()

            context['otp'] = otp
            request.session['otp'] = otp

            for htno in checkValues:
                Attendance.objects.create(student_id=Student.objects.get(hallticket_no=htno), session_id=session)

        if 'take_attendance' in request.POST:
            master = False
            classFromSelect = request.POST.getlist('selectClass')[0]
            classObj = Classes.objects.get(class_id=classFromSelect)
            context['classSelected'] = classObj
            request.session['class'] = classObj.class_id
            alreadyThere = False
            masterSession = None
            initObj = None
            for init in initlist:
                if str(init.class_id.class_id) == str(classFromSelect):
                    initObj=init
                    break
            for session in allSessions:
                if initObj == session.initiation_id:
                    if session.master:
                        alreadyThere = True
                        masterSession = session
                        master = True
                        context['master'] = True
                    break
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

def latelogin(request):
    presentClass = request.session.get('class')
    context = {}
    template = 'feedback/latelogin.html'
    if request.method == "POST":
        form = StudForm(request.POST)
        if form.is_valid():
            studid = request.POST['username']
            sessid =  request.session.get("otp")
            Attendance.create(session_id=sessid, student_id=studid)
    else:
        context['studform'] = StudForm()
    return render(request, template, context)




def student(request):

    if request.session.get('sessionObj') is not None:
        return goto_questions_page(request.session.get('maxPage'))

    template = 'feedback/student_login.html'
    context = {}
    #Are any sessions open?
    sessions = Session.objects.all().order_by('-timestamp')[:50]
    if len(sessions) == 0 or (datetime.datetime.now(datetime.timezone.utc) - sessions[0].timestamp).total_seconds()/60 > getStudentTimeout():
        return redirect('/')
    if request.method == 'POST':
        lst = request.POST.getlist('OTP')[0]
        classObj = None
        for session in sessions:
            context['lst'] = session.session_id
            if str(session.session_id) == lst:
                #Start a session and redirect to the feedback questions page
                request.session['sessionObj'] = session.session_id
                request.session['classId'] = session.initiation_id.class_id.__str__()
                return redirect('/feedback/questions')
        if classObj is None:
            context['otpError'] = 'otpError'
    return render(request, template, context)


def questions(request, category):
    session_id = request.session.get('sessionObj')
    if session_id is None:
        return redirect('/')

    maxPage = request.session.get('maxPage')
    if maxPage is None:
        maxPage = 1
        request.session['maxPage'] = 1

    template = 'feedback/questions.html'
    context = {}

    session = Session.objects.get(session_id=session_id)

    attendance = Attendance.objects.filter(session_id=session).count()
    attendanceCount = Feedback.objects.filter(session_id=session).values_list('student_no').distinct().count()
    context['attendance'] = str(attendance)+' '+str(attendanceCount)
    if attendanceCount == attendance:
        return HttpResponse("Sorry, the attendance limit has been reached.")

    #GET CATEGORY
    if category == '': category = 'faculty'
    category = Category.objects.get(category=category)
    context['category'] = category.category


    #GET CLASS OBJECT
    classObj = session.initiation_id.class_id
    context['class_obj'] = classObj

    #GET ALL THE CONTENT DETAILS - CLASSES, CFS, ETC
    paging = [0]
    subjects = []
    faculty = []
    cfsList = []
    if category.category == 'faculty' or category.category == 'LOA':
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
    try: pager = paginator.page(page)
    except PageNotAnInteger: pager = paginator.page(1)
    except EmptyPage: pager = paginator.page(paginator.num_pages)
    context['pager'] = pager
    pgno = str(pager.number)

    #CHECK IF WE ARE ON THE RIGHT PAGE NUMBER
    if pager.number != maxPage:
        return redirect('/feedback/questions/'+category.category+'/?page='+str(request.session['maxPage']))


    if category.category == 'faculty' or category.category == 'LOA':
        context['subject'] = subjects[pager.number - 1]
        context['faculty'] = faculty[pager.number - 1]

    questionsList = []
    subCategsList = []
    questionsQList = FdbkQuestions.objects.filter(category=category)
    if category.category == 'LOA':
        subCategs = questionsQList.values_list('subcategory').distinct()
        for subCateg in subCategs:
            subCategsList.append(subCateg)
        #TODO setup the relation id for the subcategory and subject
        questionsQList = questionsQList.filter(subcategory=subCategsList[pager.number-1])
    for i in questionsQList:
        questionsList.append(i)
    context['questions'] = questionsList
    currentSubCategory = ''
    subcategoryOrder = []
    for i in range(len(questionsList)):
        if questionsList[i].subcategory != currentSubCategory and questionsList[i].subcategory is not None:
            currentSubCategory = questionsList[i].subcategory
            subcategoryOrder.append(i+1)
    context['subcategory'] = subcategoryOrder

    myRating = request.session.get(pgno, None)
    if myRating is not None:
        context['allRatings'] = request.session[pgno]
    else:
        request.session[pgno] = None

    if request.method == 'POST':
        try:
            ratings = []
            for i in range(1, len(questionsList)+1):
                name = 'star' + str(i)
                value = request.POST[name]
                ratings.append(value)
            request.session[pgno] = ratings
            max = request.session.get('maxPage')
            if max is None: max = 0
            request.session['maxPage'] = max+1
        except MultiValueDictKeyError:
            context['error'] = "Please enter all the ratings"
            return render(request, template, context)


        if 'next' in request.POST:
            #return render(request, template, context)
            return redirect('/feedback/questions/'+category.category+'/?page='+str(pager.number+1))

        if 'finish' in request.POST:
            request.session['maxPage'] = 1
            student_no = Feedback.objects.filter(session_id=session, category=category)
            if len(student_no) == 0: student_no = 1
            else: student_no = student_no.order_by('-student_no')[0].student_no+1

            #GET THE REMARKS FROM HTML
            remarks = request.POST.getlist('remarks')
            if remarks is not None and len(remarks) == 1:
                remarks = Notes.objects.create(note=remarks[0], session_id=session)

            if category.category == 'faculty':
                for i in range(1, pager.end_index()+1):
                    if request.session.get(str(i)) is None or None in request.session[str(i)]:
                        return redirect('/feedback/questions/?page='+str(i))


                for i in range(0, len(cfsList)):
                    ratingsString = ""
                    for j in range(0, len(questionsList)):
                        ratingsString += str(request.session[str(i+1)][j])
                        if j != len(questionsList)-1:
                            ratingsString += ","
                    Feedback.objects.create(session_id=session, category=category, relation_id=str(cfsList[i-1].cfs_id), student_no=student_no, ratings=ratingsString)

                #del request.session['sessionObj']
                #TODO store macaddress so that this PC is not used again with the session id
                #return HttpResponse("Thank you for the most valuable review!")
                return redirect('/feedback/questions/facility')

            if category.category == 'facility':
                ratingsString = ""
                for i in range(0, len(ratings)):
                    ratingsString += str(ratings[i])
                    if i != len(ratings)-1:
                        ratingsString += ","
                Feedback.objects.create(session_id=session, category=category, student_no=student_no, ratings=ratingsString)
                #del request.session['sessionObj']
                #return HttpResponse("Thank you for the most valuable review!")
                return redirect('/feedback/questions/LOA')


    return render(request, template, context)


def initiateFor(year, branch, section, by):
    classobj = Classes.objects.get(year=year, branch=branch, section=section)
    history = Initiation.objects.filter(class_id=classobj)
    if len(history) == 0 or history[len(history) - 1].timestamp.date() != datetime.date.today():
        dt = str(datetime.datetime.now())
        Initiation.objects.create(timestamp=dt, initiated_by=by, class_id=classobj)
        return 'success'
    else: return 'failed'


def getStudentTimeout():
    try:
        timeInMin = Config.objects.get(key='studentTimeout')
        return int(timeInMin.value)
    except Exception:
        Config.objects.create(key='studentTimeout', value='5', description="Expire the student login page after these many seconds")
        return 5


def goto_questions_page(page_no, category='faculty'):
    if page_no is None:
        return redirect('/feedback/questions/')
    return redirect('/feedback/questions/'+category+'/?page='+str(page_no))


def isNotEligible(cls):
    initiations = Initiation.objects.all()
    for initiation in initiations:
        if initiation.timestamp.date() == datetime.date.today():
            if cls == initiation.class_id:
                return True

    return False