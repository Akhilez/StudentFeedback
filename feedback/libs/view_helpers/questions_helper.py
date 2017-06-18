import re
from threading import Lock
from django.shortcuts import redirect
from feedback.libs.view_helpers.conduct_helper import get_master_of
from feedback.models import Feedback, Attendance, ClassFacSub, Notes

__author__ = 'Akhil'


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
    currentSubCategory = ''
    subcategoryOrder = []
    for i in range(len(questions_list)):
        if questions_list[i].subcategory != currentSubCategory and questions_list[i].subcategory is not None:
            currentSubCategory = questions_list[i].subcategory
            subcategoryOrder.append(i + 1)
    return subcategoryOrder


def ratings_to_session_variable(request, cfsList, questionsList):
    for cfs in cfsList:
        ratingsString = ""
        for j in range(0, len(questionsList)):
            ratingsString += str(
                request.POST['star-' + str(questionsList[j].question_id) + '-' + str(cfs.cfs_id)])
            if j != len(questionsList) - 1:
                ratingsString += ","
        request.session[str(cfs.cfs_id)] = ratingsString


def questions_string_of(questions_list):
    questions = ""
    for i in range(len(questions_list)):
        questions += str(questions_list[i].question_id)
        if i != len(questions_list) - 1:
            questions += ','
    return questions


def get_finish_result(request, cfsList, questionsList, session, all_cfsList):
    """
    a. get the ratings(stars)
    b. get review(textarea) and enter into Notes table.
    c. get the student_no from the feedback table
    c.1 write ratings and questions into ratings table
    d. Enter ratings into database - for each cfs, add record
    e. redirect to faculty feedback
    :param request:
    :param cfsList:
    :param questionsList:
    :param session:
    :return: httpresponse
    """
    # a. get the ratings(stars)
    ratings_to_session_variable(request, cfsList, questionsList)

    # b. get review(textarea) and enter into Notes table.
    remarks = request.POST.getlist('remarks')
    if remarks is not None and len(remarks) == 1 and remarks[0] != '':
        Notes.objects.create(note=remarks[0], session_id=session)

    # c. get the student_no from the feedback table
    student_no = Feedback.objects.filter(session_id=session)
    student_no = 1 if len(student_no) == 0 else student_no.order_by('-student_no')[0].student_no + 1

    # d. Enter ratings into database - for each cfs, add record
    questions = questions_string_of(questionsList)
    for cfs in all_cfsList:
        Feedback.objects.create(session_id=session,
                                cfs_id=cfs, student_no=student_no,
                                ratings=request.session[str(cfs.cfs_id)], questions=questions)

    # e. redirect to faculty feedback
    del request.session['maxPage']
    #return redirect('http://facility.feedback.com/')#('/feedback/questions/facility')
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