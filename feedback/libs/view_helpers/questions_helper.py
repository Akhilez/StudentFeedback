import re
from django.shortcuts import redirect
from feedback.libs.view_helper import get_master_session
from feedback.models import Feedback, Attendance, ClassFacSub, Notes

__author__ = 'Akhil'


def attendance_from_session(session):
    attendance_count = Feedback.objects.filter(session_id=session).values_list(
                    'student_no').distinct().count()
    if session.mastersession is not None:
        attendance_count += Feedback.objects.filter(
            session_id=get_master_session(session)).values_list(
            'student_no').distinct().count()
    return attendance_count


def attendance_from_attendance(session):
    attendance = Attendance.objects.filter(session_id=session).count()
    if session.mastersession is not None:
        attendance += Attendance.objects.filter(session_id=get_master_session(session)).count()
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


def get_rating_strings(request, cfsList, questionsList):
    ratings = []
    for cfs in cfsList:
        ratingsString = ""
        for j in range(0, len(questionsList)):
            ratingsString += str(
                request.POST['star-' + str(questionsList[j].question_id) + '-' + str(cfs.cfs_id)])
            if j != len(questionsList) - 1:
                ratingsString += ","
        ratings.append(ratingsString)
    return ratings


def get_finish_result(request, cfsList, questionsList, session):
    """
    a. get the ratings(stars)
    b. get review(textarea) and enter into Notes table.
    c. get the student_no from the feedback table
    d. Enter ratings into database - for each cfs, add record
    e. redirect to faculty feedback
    :param request:
    :param cfsList:
    :param questionsList:
    :param session:
    :return: httpresponse
    """
    # a. get the ratings(stars)
    ratings = get_rating_strings(request, cfsList, questionsList)

    # b. get review(textarea) and enter into Notes table.
    remarks = request.POST.getlist('remarks')
    if remarks is not None and len(remarks) == 1 and remarks[0] != '':
        Notes.objects.create(note=remarks[0], session_id=session)

    # c. get the student_no from the feedback table
    student_no = Feedback.objects.filter(session_id=session)
    student_no = 1 if len(student_no) == 0 else student_no.order_by('-student_no')[0].student_no + 1

    # d. Enter ratings into database - for each cfs, add record
    for i in range(0,len(cfsList)):
        Feedback.objects.create(session_id=session,
                                relation_id=str(cfsList[i].cfs_id), student_no=student_no,
                                ratings=ratings[i])

    # e. redirect to faculty feedback
    #return redirect('http://facility.feedback.com/')#('/feedback/questions/facility')
    return redirect('/feedback/LoaQuestions')