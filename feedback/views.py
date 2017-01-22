from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.datastructures import MultiValueDictKeyError
from StudentFeedback.settings import COORDINATOR_GROUP, CONDUCTOR_GROUP, LOGIN_URL
from feedback.forms import LoginForm
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

    allInits = Initiation.objects.all()
    initlist = []
    for i in allInits:
        if i.timestamp.date() == datetime.date.today():
            initlist.append(i)
    if len(initlist) != 0:
        context['classes'] = initlist

    if request.method == 'POST' :
        if 'confirmSession' in request.POST:
            classFromSelect = request.session.get('class', None)
            if classFromSelect is None:
                return HttpResponse("None")
            checkValues = request.POST.getlist("attendanceList")

            otp = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
            dt = str(datetime.datetime.now())
            initObj = None
            for init in initlist:
                if str(init.class_id.class_id) == str(classFromSelect):
                    initObj=init
                    break
            context['classSelected'] = initObj.class_id
            session = Session.objects.create(timestamp=dt, taken_by=request.user, initiation_id=initObj, session_id=otp)
            context['otp'] = otp
            request.session['otp'] = otp


            for htno in checkValues:
                Attendance.objects.create(student_id=Student.objects.get(hallticket_no=htno), session_id=session)

        if 'take_attendance' in request.POST:
            classFromSelect = request.POST.getlist('selectClass')[0]
            classObj = Classes.objects.get(class_id=classFromSelect)
            context['classSelected'] = classObj
            request.session['class'] = classObj.class_id
            allStudents = Student.objects.filter(class_id=classObj)
            context['allStudetns'] = allStudents

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

    template = 'feedback/questions.html'
    context = {}

    session = Session.objects.get(session_id=session_id)

    attendance = Attendance.objects.filter(session_id=session).count()
    attendanceCount = Feedback.objects.filter(session_id=session).values_list('student_no').distinct().count()
    context['attendance'] = str(attendance)+' '+str(attendanceCount)
    if attendanceCount == attendance:
        return HttpResponse("Sorry, the attendance limit has been reached.")


    if category == '': category = 'faculty'
    category = Category.objects.get(category=category)
    context['category'] = category.category


    classObj = session.initiation_id.class_id
    context['class_obj'] = classObj
    cfsList = []

    questionsList = []
    questionsQList = FdbkQuestions.objects.filter(category=category)
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

    paging = [0]
    subjects = []
    faculty = []
    if category.category == 'faculty':
        cfs = ClassFacSub.objects.filter(class_id=classObj)
        for i in cfs:
            cfsList.append(i)
            subjects.append(i.subject_id.name)
            faculty.append(i.faculty_id)
            context['subjects'] = subjects
        paging = subjects

    paginator = Paginator(paging, 1)

    page = request.GET.get('page')
    try: pager = paginator.page(page)
    except PageNotAnInteger: pager = paginator.page(1)
    except EmptyPage: pager = paginator.page(paginator.num_pages)

    if pager.number != request.session['maxPage']:
        return redirect('/feedback/questions/?page='+str(request.session['maxPage']))

    context['pager'] = pager
    pgno = str(pager.number)

    if category.category == 'faculty':
        context['subject'] = subjects[pager.number - 1]
        context['faculty'] = faculty[pager.number - 1]


    myRating = request.session.get(pgno, None)
    if myRating is not None:
        #TODO display all the ratings in HTML
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
            return redirect('/feedback/questions/?page='+str(pager.number+1))

        if 'finish' in request.POST:
            student_no = Feedback.objects.filter(session_id=session)
            if len(student_no) == 0: student_no = 1
            else: student_no = student_no.order_by('-student_no')[0].student_no+1

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
                    Feedback.objects.create(session_id=session, category=category, relation_id=cfsList[i-1], student_no=student_no, ratings=ratingsString)

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
                del request.session['sessionObj']
                return HttpResponse("Thank you for the most valuable review!")


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

def goto_questions_page(page_no):
    if page_no is None:
        return redirect('/feedback/questions/')
    return redirect('/feedback/questions/?page='+str(page_no))
