import re

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect, render

from feedback.libs import view_helper
from feedback.libs.config_helper import get_max_subjects_each_page_loa
from feedback.models import *

__author__ = 'Akhil'


def get_view(request):
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
    all_subjects = get_all_subjects(class_obj)
    max_sub_each = get_max_subjects_each_page_loa()

    # 2. make pagination
    pager = get_pager(request, all_subjects, max_sub_each)
    context['pager'] = pager

    # 3. get maxPage if exists else create maxPage
    if set_max_page(request, pager.number):
        return redirect('/feedback/LoaQuestions/?page=' + str(request.session['maxPage'][0]))

    # get the pager indices
    context['page_index_list'] = [i for i in range(1, max_sub_each + 1)]

    # 4. get the subjects for current page
    subjects = all_subjects[((pager.number - 1) * max_sub_each): (pager.number * max_sub_each)]

    # 5. for each subject obj, get its questions, make a SubQues object and pass it to context
    sub_ques_list = get_sub_ques_list(subjects)
    context['sub_ques_list'] = sub_ques_list

    if request.method == 'POST':
        # 6. handle next button click
        if 'next' in request.POST:
            return next_button_result(request, context)

        # 7. handle submit button click
        if 'submit' in request.POST:
            return submit_button_result(request, context, session, all_subjects)

    return render(request, template, context)


class SubQues:
    def __init__(self, subject, questions):
        self.subject = subject
        self.questions = questions
        self.ratings = []


def ratings_to_session_variable(context, request):
    """
    1. for each sub ques, question, get the star id value.
    2. for each sub ques, enter the ratings into session variable
    :param context:
    :param request:
    :return:
    """
    for sub_ques in context['sub_ques_list']:
        for question in sub_ques.questions:
            sub_ques.ratings.append(
                request.POST["star-" + str(sub_ques.subject.subject_id) + "-" + str(question.question_id)]
            )
        # 2. for each sub ques, enter the ratings into session variable
        request.session[sub_ques.subject.name] = sub_ques.ratings


def next_button_result(request, context):
    """
    1. for each sub ques, question, get the star id value.
    2. for each sub ques, enter the ratings into session variable
    3. redirect to next page.
    :param request:
    :param context:
    :return:
    """
    # 1. for each sub ques, question, get the star id value.
    # 2. for each sub ques, enter the ratings into session variable
    ratings_to_session_variable(context, request)

    # 3. redirect to next page.
    request.session['maxPage'][0] += 1
    return redirect(('/feedback/LoaQuestions/?page=' + str(context['pager'].number + 1)))


def rating_string_from_array(array):
    rating = ""
    for i in range(len(array)):
        rating += array[i]
        if i != (len(array) - 1):
            rating += ','
    return rating


def get_questions_string(questions, subject):
    questions = questions.filter(subject_id=subject)
    question_string = ""
    for i in range(len(questions)):
        question_string += str(questions[i].question_id)
        if i != len(questions) - 1:
            question_string += ','
    return question_string


def submit_button_result(request, context, session, subjects):
    """
    1. for each sub ques, question, get the star id value.
    2. for each sub ques, enter the ratings into session variable
    3. get student no.
    4. for each subject enter ratings into table
    5. deleting session
    6. Adding cookie for facility
    :param request:
    :param context:
    :return: response
    """
    # 1. for each sub ques, question, get the star id value.
    # 2. for each sub ques, enter the ratings into session variable
    ratings_to_session_variable(context, request)

    # 3. get student no.
    student_no = FeedbackLoa.objects.filter(session_id=session)
    student_no = 1 if len(student_no) == 0 else student_no.order_by('-student_no')[0].student_no + 1

    # 4. for each subject enter ratings into table
    questions = LOAquestions.objects.filter(enabled=True)
    for sub in subjects:
        questions_string = get_questions_string(questions, sub)
        if questions_string == "":
            continue
        FeedbackLoa.objects.create(session_id=session, student_no=student_no,
                                   subject_id=sub,
                                   ratings=rating_string_from_array(request.session[sub.name]),
                                   questions=questions_string)

    return view_helper.get_next_fdbk_response(request)


def get_sub_ques_list(subjects):
    sub_ques_list = []
    for subject in subjects:
        sub_ques_list.append(
            SubQues(
                subject,
                [i for i in LOAquestions.objects.filter(subject_id=subject, enabled=True)]
            )
        )
    return sub_ques_list


def get_all_subjects(class_obj):
    all_subjects = []
    for cfs in ClassFacSub.objects.filter(class_id=class_obj):
        if not re.compile("^.* [Ll][Aa][Bb]$").match(cfs.subject_id.name) and not re.compile(
                "[Mm][eE][nN][tT][oO][rR][iI][nN][gG]").match(cfs.subject_id.name):
            all_subjects.append(cfs.subject_id)
    all_subjects.insert(0, Subject.objects.filter(name="General Objectives")[0])
    return all_subjects


def get_pager(request, all_subjects, max_sub_each):
    paginator = Paginator(all_subjects, max_sub_each)
    page = request.GET.get('page')
    try:
        pager = paginator.page(page)
    except PageNotAnInteger:
        pager = paginator.page(1)
    except EmptyPage:
        pager = paginator.page(paginator.num_pages)
    return pager


def set_max_page(request, pager_number):
    max_page = request.session.get('maxPage')
    if max_page is None:
        max_page = [1, 'LOA']
        request.session['maxPage'] = max_page
    if pager_number != max_page[0]:
        return True
    return False
