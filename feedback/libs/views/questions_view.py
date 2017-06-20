import re
from django.http import HttpResponse
from django.shortcuts import redirect, render
from feedback.libs.config_helper import get_max_cfs_each
from feedback.libs.view_helper import get_master_of
from feedback.libs.views import loa_questions_view
from feedback.models import Session, FdbkQuestions, Feedback, Attendance, ClassFacSub, Notes

__author__ = 'Akhil'


def get_view(request):
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
    if attendance_from_session(session) >= attendance_from_attendance(session):
        del request.session['sessionObj']
        return HttpResponse("Sorry, the attendance limit has been reached.")

    # get necessary details
    all_cfs_list = get_cfs_for(class_id=session.initiation_id.class_id)
    max_cfs_each = get_max_cfs_each()

    # 2.1 make pagination
    pager = loa_questions_view.get_pager(request, all_cfs_list, max_cfs_each)
    context['pager'] = pager

    # 2.2 get maxPage if exists else create maxPage
    if set_max_page(request, pager.number):
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
    context['subcategory'] = get_subcategory_order(questions_list)

    # 6. Handle finish button:
    if request.method == 'POST':
        if 'next' in request.POST:
            return get_next_result(request, cfs_list, questions_list, pager)

        if 'finish' in request.POST:
            return get_finish_result(request, cfs_list, questions_list, session, all_cfs_list)

    return render(request, template, context)


def attendance_from_session(session):
    attendance_count = Feedback.objects.filter(session_id=session).values_list(
        'student_no').distinct().count()
    if get_master_of(session) is not None:
        attendance_count += Feedback.objects.filter(
            session_id=get_master_of(session)).values_list(
            'student_no').distinct().count()
    return attendance_count


def attendance_from_attendance(session):
    attendance = Attendance.objects.filter(session_id=session).count()
    if get_master_of(session) is not None:
        attendance += Attendance.objects.filter(session_id=get_master_of(session)).count()
    return attendance


def get_cfs_for(class_id):
    cfs_list = []
    for cfs in ClassFacSub.objects.filter(class_id=class_id):
        if not re.compile("^.* [Ll][Aa][Bb]$").match(cfs.subject_id.name) and not re.compile(
                "[Mm][eE][nN][tT][oO][rR][iI][nN][gG]").match(cfs.subject_id.name):
            cfs_list.append(cfs)
    return cfs_list


def get_subcategory_order(questions_list):
    current_sub_category = ''
    subcategory_order = []
    for i in range(len(questions_list)):
        if questions_list[i].subcategory != current_sub_category and questions_list[i].subcategory is not None:
            current_sub_category = questions_list[i].subcategory
            subcategory_order.append(i + 1)
    return subcategory_order


def ratings_to_session_variable(request, cfs_list, questions_list):
    for cfs in cfs_list:
        ratings_string = ""
        for j in range(0, len(questions_list)):
            ratings_string += str(
                request.POST['star-' + str(questions_list[j].question_id) + '-' + str(cfs.cfs_id)])
            if j != len(questions_list) - 1:
                ratings_string += ","
        request.session[str(cfs.cfs_id)] = ratings_string


def questions_string_of(questions_list):
    questions = ""
    for i in range(len(questions_list)):
        questions += str(questions_list[i].question_id)
        if i != len(questions_list) - 1:
            questions += ','
    return questions


def get_finish_result(request, cfs_list, questions_list, session, all_cfs_list):
    """
    a. get the ratings(stars)
    b. get review(textarea) and enter into Notes table.
    c. get the student_no from the feedback table
    c.1 write ratings and questions into ratings table
    d. Enter ratings into database - for each cfs, add record
    e. redirect to faculty feedback
    :param request:
    :param cfs_list:
    :param questions_list:
    :param session:
    :return: httpresponse
    """
    # a. get the ratings(stars)
    ratings_to_session_variable(request, cfs_list, questions_list)

    # b. get review(textarea) and enter into Notes table.
    remarks = request.POST.getlist('remarks')
    if remarks is not None and len(remarks) == 1 and remarks[0] != '':
        Notes.objects.create(note=remarks[0], session_id=session)

    # c. get the student_no from the feedback table
    student_no = Feedback.objects.filter(session_id=session)
    student_no = 1 if len(student_no) == 0 else student_no.order_by('-student_no')[0].student_no + 1

    # d. Enter ratings into database - for each cfs, add record
    questions = questions_string_of(questions_list)
    for cfs in all_cfs_list:
        Feedback.objects.create(session_id=session,
                                cfs_id=cfs, student_no=student_no,
                                ratings=request.session[str(cfs.cfs_id)], questions=questions)

    # e. redirect to faculty feedback
    del request.session['maxPage']
    # return redirect('http://facility.feedback.com/')#('/feedback/questions/facility')
    return redirect('/feedback/LoaQuestions')


def set_max_page(request, pager_number):
    max_page = request.session.get('maxPage')
    if max_page is None:
        max_page = [1, 'faculty']
        request.session['maxPage'] = max_page
    if pager_number != max_page[0]:
        return True
    return False


def get_next_result(request, cfs_list, questions_list, pager):
    ratings_to_session_variable(request, cfs_list, questions_list)

    request.session['maxPage'][0] += 1
    return redirect(('/feedback/questions/?page=' + str(pager.number + 1)))