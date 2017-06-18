from feedback.models import *

formatter = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV', }
deformatter = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', }


def get_selected_questions():
    return Timeline.selected_questions


class Timeline:
    selected_questions = [x for x in range(len(FdbkQuestions.objects.values_list('question')))]

    def __init__(self, date, rating):
        self.date = date
        self.rating = rating

    def __str__(self):
        return str(self.date) + self.rating


def get_years():
    years = Classes.objects.values_list('year').distinct().order_by('year')
    return [formatter[str(x[0])] for x in years]


def get_branches(year):
    classes = Classes.objects.filter(year=int(deformatter[year]))
    branches = []
    for cls in classes:
        if cls.branch in branches:
            continue
        cfss = ClassFacSub.objects.filter(class_id=cls)
        for cfs in cfss:
            if cfs.cfs_id in get_fdbk_cfs():
                branches.append(cls.branch)
                break

    return branches


def get_sections(year, branch):
    classes = Classes.objects.filter(year=int(deformatter[year]), branch=branch)
    sections = []
    for cls in classes:
        if cls.section in sections:
            continue
        cfss = ClassFacSub.objects.filter(class_id=cls)
        for cfs in cfss:
            if cfs.cfs_id in get_fdbk_cfs():
                sections.append(cls.section)
                break

    return sections


def get_faculty(year, branch, section):
    classes = Classes.objects.filter(year=int(deformatter[year]), branch=branch, section=section)
    cfs = ClassFacSub.objects.all()
    subjects = []
    for cls in classes:
        subs = cfs.filter(class_id=cls)
        for sub in subs:
            if sub.cfs_id in get_fdbk_cfs():
                sub_name = sub.faculty_id
                if sub_name not in subjects:
                    subjects.append(sub_name)
    return subjects


def get_average(summ, itr, session=None, rel=None):
    if rel is None:
        feedbacks = Feedback.objects.filter(session_id=session)
    else:
        feedbacks = Feedback.objects.filter(relation_id=rel)
    for feedback in feedbacks:
        ratings = feedback.ratings.split(',')
        for i in range(len(ratings)):
            if i in Timeline.selected_questions:
                summ += int(ratings[i])
                itr += 1
    return summ, itr


def get_year_value(year):
    classes = Classes.objects.filter(year=deformatter[year])
    sum = 0
    itr = 0
    for cls in classes:
        initiations = Initiation.objects.filter(class_id=cls)
        for initiation in initiations:
            sessions = Session.objects.filter(initiation_id=initiation)
            for session in sessions:
                (sum, itr) = get_average(sum, itr, session=session)
    if itr != 0:
        avg = sum / itr
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
                (sum, itr) = get_average(sum, itr, session=session)
    if itr != 0:
        avg = sum / itr
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
                (sum, itr) = get_average(sum, itr, session=session)
    if itr != 0:
        avg = sum / itr
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
    (sum, itr) = get_average(sum, itr, rel=cfs.cfs_id)
    if itr != 0:
        avg = sum / itr
    else:
        avg = 0.0
    return avg


def get_all_faculty():
    faculty = Faculty.objects.all()
    faculty_set = []
    for fac in faculty:
        cfss = ClassFacSub.objects.filter(faculty_id=fac)
        for cfs in cfss:
            if cfs.cfs_id in get_fdbk_cfs():
                faculty_set.append(fac)
                break
    return faculty_set


def get_all_subjects():
    subjects = Subject.objects.all().values_list('name')
    return [subject[0] for subject in subjects]


def get_faculty_value(faculty):
    sum = 0
    itr = 0
    cfss = ClassFacSub.objects.filter(faculty_id=faculty)
    for cfs in cfss:
        (sum, itr) = get_average(sum, itr, rel=cfs.cfs_id)
    if itr != 0:
        avg = sum / itr
    else:
        avg = 0.0
    return avg


def get_all_question_texts():
    questions = FdbkQuestions.objects.all()
    return [question for question in questions]


def get_question_value(faculty, question):
    question_number = get_question_number(question, 'faculty')
    if question_number == -1:
        return 0
    sum = 0
    itr = 0
    cfss = ClassFacSub.objects.filter(faculty_id=Faculty.objects.get(name=faculty))
    for cfs in cfss:
        feedbacks = Feedback.objects.filter(relation_id=cfs.cfs_id)
        for feedback in feedbacks:
            ratings = feedback.ratings.split(',')
            sum += int(ratings[question_number])
            itr += 1
    if itr != 0:
        avg = sum / itr
    else:
        avg = 0.0
    return avg


def get_question_number(question, category):
    questions = FdbkQuestions.objects.all()
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
    subject_list = []
    for subject in subjects:
        if subject.name in subject_list:
            continue
        cfss = ClassFacSub.objects.filter(subject_id=subject)
        for cfs in cfss:
            if cfs.cfs_id in get_fdbk_cfs():
                subject_list.append(subject.name)
    return subject_list


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
        (sum, itr) = get_average(sum, itr, rel=cfs.cfs_id)
    if itr != 0:
        avg = sum / itr
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
        (sum, itr) = get_average(sum, itr, rel=cfs.cfs_id)
    if itr != 0:
        avg = sum / itr
    else:
        avg = 0.0
    return avg


def get_subjects(year, branch):
    classes = Classes.objects.filter(year=int(deformatter[year]), branch=branch)
    cfs = ClassFacSub.objects.all()
    subjects = set()
    for cls in classes:
        subs = cfs.filter(class_id=cls)
        for sub in subs:
            subjects.add(sub.subject_id)
    return subjects


def get_faculty_name(faculty_id):
    return Faculty.objects.get(faculty_id=faculty_id).name


def get_fdbk_cfs():
    cfs = Feedback.objects.all().values_list('relation_id').distinct()
    cfs = [int(x[0]) for x in cfs]
    return cfs


def get_faculty_cfs(faculty):
    cfss = ClassFacSub.objects.filter(faculty_id=Faculty.objects.get(name=faculty))
    cfs_list = []
    for cfs in cfss:
        if cfs.cfs_id in get_fdbk_cfs():
            cfs_list.append(cfs)
    return cfs_list


def get_question_value_for_cfs(cfs, question):
    question_number = get_question_number(question, 'faculty')
    if question_number == -1:
        return 0
    sum = 0
    itr = 0

    feedbacks = Feedback.objects.filter(relation_id=cfs)
    for feedback in feedbacks:
        ratings = feedback.ratings.split(',')
        sum += int(ratings[question_number])
        itr += 1
    if itr != 0:
        avg = sum / itr
    else:
        avg = 0.0
    return avg


def get_all_timelines(faculty):
    faculty = Faculty.objects.get(name=faculty)
    cfss = ClassFacSub.objects.filter(faculty_id=faculty)
    timelines = []
    timeline_objs = []
    for cfs in cfss:
        for feedback in Feedback.objects.filter(relation_id=cfs.cfs_id):
            my_date = feedback.session_id.timestamp.date()
            if my_date in timelines:
                continue
            timelines.append(my_date)
    for cfs in cfss:
        for timeline in timelines:
            summ = 0
            itr = 0
            for feedback in Feedback.objects.filter(relation_id=cfs.cfs_id):
                if feedback.session_id.timestamp.date() == timeline:
                    ratings = feedback.ratings.split(',')
                    for i in range(len(ratings)):
                        if i in Timeline.selected_questions:
                            summ += int(ratings[i])
                            itr += 1
            if itr == 0:
                avg = 0.0
            else:
                avg = summ / itr
            timeline_objs.append(Timeline(timeline, avg))

    return timeline_objs
