
from feedback.models import *

formatter = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV', }
deformatter = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', }


def get_years():
    years = Classes.objects.values_list('year').distinct().order_by('year')

    return [formatter[str(x[0])] for x in years]


def get_branches(year):
    branches = Classes.objects.filter(year=int(deformatter[year])).values_list('branch').order_by('branch').distinct()
    return [x[0] for x in branches]


def get_sections(year, branch):
    sections = Classes.objects.filter(year=int(deformatter[year]), branch=branch).values_list('section').order_by('branch').distinct()
    return [x[0] for x in sections]


def get_faculty(year, branch, section):
    classes = Classes.objects.filter(year=int(deformatter[year]), branch=branch, section=section)
    cfs = ClassFacSub.objects.all()
    subjects = []
    for cls in classes:
        subs = cfs.filter(class_id=cls)
        for sub in subs:
            sub_name = sub.faculty_id.name
            if sub_name not in subjects:
                subjects.append(sub_name)
    return subjects


def get_year_value(year):
    classes = Classes.objects.filter(year=deformatter[year])
    sum = 0
    itr = 0
    for cls in classes:
        initiations = Initiation.objects.filter(class_id=cls)
        for initiation in initiations:
            sessions = Session.objects.filter(initiation_id=initiation)
            for session in sessions:
                feedbacks = Feedback.objects.filter(session_id=session, category=Category.objects.get(category='faculty'))
                for feedback in feedbacks:
                    ratings = feedback.ratings.split(',')
                    for rating in ratings:
                        sum += int(rating)
                        itr += 1
    if itr != 0:
        avg = sum/itr
    else:
        avg = 0.0
    return avg

def get_branch_value(year, branch):
    classes = Classes.objects.filter(year=deformatter[year], branch=branch)
    sum = 0
    itr = 0
    for cls in classes:
        initiations = Initiation.objects.filter(class_id=cls)
        for initiation in initiations:
            sessions = Session.objects.filter(initiation_id=initiation)
            for session in sessions:
                feedbacks = Feedback.objects.filter(session_id=session, category=Category.objects.get(category='faculty'))
                for feedback in feedbacks:
                    ratings = feedback.ratings.split(',')
                    for rating in ratings:
                        sum += int(rating)
                        itr += 1
    if itr != 0:
        avg = sum/itr
    else:
        avg = 0.0
    return avg

def get_section_value(year, branch, section):
    classes = Classes.objects.filter(year=deformatter[year], branch=branch, section=section)
    sum = 0
    itr = 0
    for cls in classes:
        initiations = Initiation.objects.filter(class_id=cls)
        for initiation in initiations:
            sessions = Session.objects.filter(initiation_id=initiation)
            for session in sessions:
                feedbacks = Feedback.objects.filter(session_id=session, category=Category.objects.get(category='faculty'))
                for feedback in feedbacks:
                    ratings = feedback.ratings.split(',')
                    for rating in ratings:
                        sum += int(rating)
                        itr += 1
    if itr != 0:
        avg = sum/itr
    else:
        avg = 0.0
    return avg

def get_cfs(faculty, year, branch, section):
    cls = Classes.objects.get(year=deformatter[year], branch=branch, section=section)
    cfs_list = []
    cfss = ClassFacSub.objects.filter(class_id=cls, faculty_id=Faculty.objects.get(name=faculty))
    for cfs in cfss:
        cfs_list.append(cfs)
    return cfs_list

def get_cfs_value(cfs):
    sum = 0
    itr = 0
    feedbacks = Feedback.objects.filter(relation_id=cfs.cfs_id, category=Category.objects.get(category='faculty'))
    for feedback in feedbacks:
        ratings = feedback.ratings.split(',')
        for rating in ratings:
            sum += int(rating)
            itr += 1
    if itr != 0:
        avg = sum/itr
    else:
        avg = 0.0
    return avg

def get_all_faculty():
    facultys = Faculty.objects.all().values_list('name')
    return [faculty[0] for faculty in facultys]

def get_all_subjects():
    subjects = Subject.objects.all().values_list('name')
    return [subject[0] for subject in subjects]


def get_faculty_value(faculty):
    sum = 0
    itr = 0
    cfss = ClassFacSub.objects.filter(faculty_id=Faculty.objects.get(name=faculty))
    for cfs in cfss:
        feedbacks = Feedback.objects.filter(relation_id=cfs.cfs_id, category=Category.objects.get(category='faculty'))
        for feedback in feedbacks:
            ratings = feedback.ratings.split(',')
            for rating in ratings:
                sum += int(rating)
                itr += 1
    if itr != 0:
        avg = sum/itr
    else:
        avg = 0.0
    return avg



def get_all_question_texts():
    questions = FdbkQuestions.objects.filter(category=Category.objects.get(category='faculty'))
    return [question for question in questions]


def get_question_value(faculty, question):
    question_number = get_question_number(question, 'faculty')
    if question_number == -1:
        return 0
    sum = 0
    itr = 0
    cfss = ClassFacSub.objects.filter(faculty_id=Faculty.objects.get(name=faculty))
    for cfs in cfss:
        feedbacks = Feedback.objects.filter(relation_id=cfs.cfs_id, category=Category.objects.get(category='faculty'))
        for feedback in feedbacks:
            ratings = feedback.ratings.split(',')
            sum += int(ratings[question_number])
            itr += 1
    if itr != 0:
        avg = sum/itr
    else:
        avg = 0.0
    return avg


def get_question_number(question, category):
    questions = FdbkQuestions.objects.filter(category=Category.objects.get(category=category))
    for i in range(len(questions)):
        if questions[i] == question:
            return i
    return -1


def get_all_year_branches():
    return Classes.objects.values_list('year', 'branch')

def get_all_year_sections():
    return Classes.objects.values_list('year', 'branch', 'section')

def get_all_subjects_all_years():
    subjects = Subject.objects.all()
    subjects = [subject.name for subject in subjects]
    subjects.sort()
    return subjects

def get_subject_value(subject):
    """
    :param subject:
     get subject_id from Subject
     get cfs_id from CFS using subject_id
     get feedback from Feedback using cfs_id
     calculate avg
    :return: avg
    """
    sum = 0
    itr = 0
    subject = Subject.objects.get(name=subject)
    cfss = ClassFacSub.objects.filter(subject_id=subject)
    for cfs in cfss:
        feedbacks = Feedback.objects.filter(relation_id=cfs.cfs_id)
        for feedback in feedbacks:
            ratings_list = feedback.ratings.split(",")
            for rating in ratings_list:
                sum += int(rating)
                itr += 1
    if itr != 0:
        avg = sum/itr
    else:
        avg = 0.0
    return avg

def get_faculty_for_subject(subject):
    subject = Subject.objects.get(name=subject)
    cfss = ClassFacSub.objects.filter(subject_id=subject).values_list('faculty_id').distinct()
    cfss = [x[0] for x in cfss]
    faculty = []
    for cfs in cfss:
        faculty.append(Faculty.objects.get(faculty_id=cfs))
    return faculty

def get_faculty_value_for_subject(subject, faculty):
    """
    :param subject:
    :param faculty:
     get cfs for the subject, faculty
     get feedback for each cfs
     find avg
    :return: avg
    """
    sum = 0
    itr = 0
    subject = Subject.objects.get(name=subject)
    cfss = ClassFacSub.objects.filter(subject_id=subject, faculty_id=faculty)
    for cfs in cfss:
        feedbacks = Feedback.objects.filter(relation_id=cfs.cfs_id)
        for feedback in feedbacks:
            ratings = feedback.ratings.split(',')
            for rating in ratings:
                sum += int(rating)
                itr += 1
    if itr != 0:
        avg = sum/itr
    else:
        avg = 0.0
    return avg








