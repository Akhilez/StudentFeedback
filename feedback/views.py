from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect
from StudentFeedback.settings import COORDINATOR_GROUP, CONDUCTOR_GROUP, LOGIN_URL
from feedback.forms import LoginForm
from django.contrib.auth.decorators import login_required
from feedback.models import Classes, Initiation, Session
import datetime


def login_redirect(request):
    return redirect(LOGIN_URL)


def login_view(request):
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
def initiate(request, year, branch, section):
    if not request.user.groups.filter(name=COORDINATOR_GROUP).exists():
        return HttpResponse("You don't have permissions to view this page")

    context = {'total_history': Initiation.objects.all().order_by('-timestamp')[:10]}
    template = 'feedback/initiate.html'

    years = Classes.objects.order_by('year').values_list('year').distinct()  # returns a list of tuples
    years = [years[x][0] for x in range(len(years))]  # makes a list of first element of tuples in years
    context['years'] = years
    context['allYears'] = years


    # Dynamic dropdowns
    if year != '':
        context['selectedYear'] = year
        branches = Classes.objects.filter(year=year).values_list('branch').order_by('branch').distinct()
        context['branches'] = branches
    if year != '' and branch != '':
        context['selectedBranch'] = branch
        sections = Classes.objects.filter(year=year, branch=branch).values_list('section').order_by(
            'section').distinct()
        context['sections'] = sections
    if year != '' and branch != '' and section != '':
        context['selectedSection'] = section
        classobj = Classes.objects.get(year=year, branch=branch, section=section)
        history = Initiation.objects.filter(class_id=classobj).order_by('-timestamp')
        context['history'] = history
        if len(history) == 0 or history[0].timestamp.date() != datetime.date.today():
            context['isEligible'] = 'true'
        if request.method == 'POST' and 'confirmSingle' in request.POST:
            dt = str(datetime.datetime.now())
            Initiation.objects.create(timestamp=dt, initiated_by=request.user, class_id=classobj)
            context['submitted'] = 'done'


    #handling the submit buttons
    if request.method == 'POST':
        if 'nextBranch' in request.POST:
            selectedYears = request.POST.getlist('class')
            allClasses = {}
            yrs_lst = []
            for yrrr in selectedYears:
                branches = Classes.objects.filter(year=yrrr).values_list('branch').order_by('year').distinct()
                branches = [branches[x][0] for x in range(len(branches))]
                allClasses[yrrr] = branches
                for i in range(len(branches)):
                    yrs_lst.append(yrrr)
            context['fewBranches'] = allClasses
            context['years'] = yrs_lst

        if 'nextSection' in request.POST:
            allClasses = Classes.objects.all()
            checkedList = request.POST.getlist('class')
            selectedYears = []
            selectedBranches = []
            completeList = [[], [], []]
            for i in checkedList:
                splitList = i.split('-')
                selectedYears.append(splitList[0])
                selectedBranches.append(splitList[1])

            for i in range(len(checkedList)):
                sections = allClasses.filter(year=selectedYears[i], branch=selectedBranches[i]).values_list(
                    'section').order_by('year')
                sections = [sections[x][0] for x in range(len(sections))]
                for sec in sections:
                    completeList[0].append(selectedYears[i])
                    completeList[1].append(selectedBranches[i])
                    completeList[2].append(sec)
            transList = []
            for i in range(len(completeList[0])):
                inst = [completeList[0][i], completeList[1][i], completeList[2][i]]
                transList.append(inst)
            context['completeList'] = transList

        if 'confirmSelected' in request.POST:
            checkedList = request.POST.getlist('class')
            lst = []
            for i in checkedList:
                inst = i.split('-')
                status = initiateFor(inst[0], inst[1], inst[2], request.user)
                lst.append(inst[0]+inst[1]+inst[2]+" - "+status)
            context['status'] = lst




    # Are any sessions open?
    currectSessions = Session.objects.filter(timestamp=datetime.date.today())
    context['curs'] = currectSessions


    return render(request, template, context)


@login_required
def conduct(request):
    if not request.user.groups.filter(name=CONDUCTOR_GROUP).exists():
        return HttpResponse("You don't have permissions to view this page")
    return render(request, 'feedback/conduct.html')


def initiateFor(year, branch, section, by):
    classobj = Classes.objects.get(year=year, branch=branch, section=section)
    history = Initiation.objects.filter(class_id=classobj)
    if len(history) == 0 or history[len(history) - 1].timestamp.date() != datetime.date.today():
        dt = str(datetime.datetime.now())
        Initiation.objects.create(timestamp=dt, initiated_by=by, class_id=classobj)
        return 'success'
    else:
        return 'failed'
