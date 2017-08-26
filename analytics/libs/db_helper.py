from feedback.models import *

formatter = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV', }
deformatter = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', }


class Timeline:
    selected_questions = []

    def __init__(self, date, rating):
        self.date = date
        self.rating = rating

    @staticmethod
    def get_selected_questions():
        if len(Timeline.selected_questions) == 0:
            Timeline.selected_questions = [int(x[0]) for x in FdbkQuestions.objects.filter(enabled=True).values_list('question_id')]
        return Timeline.selected_questions

    @staticmethod
    def set_selected_questions(questions_list):
        Timeline.selected_questions = questions_list

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
        feedbacks = Feedback.objects.filter(cfs_id=rel)
    for feedback in feedbacks:
        ratings = feedback.ratings.split(',')
        for i in range(len(ratings)):
            if i in Timeline.get_selected_questions():
                summ += int(ratings[i])
                itr += 1
    return summ, itr


def get_avg_of(feedback):
    total = 0
    itr = 0
    rating_dict = create_dict(feedback)
    for q_id in Timeline.get_selected_questions():
        try:
            total += rating_dict[int(q_id)]
            itr += 1
        except KeyError:
            continue
    return total/itr if itr != 0 else 0.0


def get_year_value(year):
    total = 0
    itr = 0
    for cls in Classes.objects.filter(year=deformatter[year]):
        for initiation in Initiation.objects.filter(class_id=cls):
            for session in Session.objects.filter(initiation_id=initiation):
                for feedback in Feedback.objects.filter(session_id=session):
                    total += get_avg_of(feedback)
                    itr += 1
    return total/itr if itr != 0 else 0.0


def get_branch_value(year, branch):
    total = 0
    itr = 0
    for cls in Classes.objects.filter(year=deformatter[year], branch=branch):
        for initiation in Initiation.objects.filter(class_id=cls):
            for session in Session.objects.filter(initiation_id=initiation):
                for feedback in Feedback.objects.filter(session_id=session):
                    total += get_avg_of(feedback)
                    itr += 1
    return total/itr if itr != 0 else 0.0


def get_section_value(year, branch, section):
    total = 0
    itr = 0
    for cls in Classes.objects.filter(year=deformatter[year], branch=branch, section=section):
        for initiation in Initiation.objects.filter(class_id=cls):
            for session in Session.objects.filter(initiation_id=initiation):
                for feedback in Feedback.objects.filter(session_id=session):
                    total += get_avg_of(feedback)
                    itr += 1
    return total/itr if itr != 0 else 0.0


def get_cfs(faculty, year, branch, section):
    cls = Classes.objects.get(year=deformatter[year], branch=branch, section=section)
    cfs_list = []
    cfss = ClassFacSub.objects.filter(class_id=cls, faculty_id=Faculty.objects.get(name=faculty))
    for cfs in cfss:
        cfs_list.append(cfs)
    return cfs_list


def get_cfs_value(cfs):
    total = 0
    itr = 0
    for feedback in Feedback.objects.filter(cfs_id=cfs.cfs_id):
            total += get_avg_of(feedback)
            itr += 1
    return total/itr if itr != 0 else 0.0


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
    total = 0
    itr = 0
    cfss = ClassFacSub.objects.filter(faculty_id=faculty)
    for cfs in cfss:
        for feedback in Feedback.objects.filter(cfs_id=cfs.cfs_id):
            total += get_avg_of(feedback)
            itr += 1
    return total/itr if itr != 0 else 0.0


def get_all_question_texts():
    return [x for x in FdbkQuestions.objects.filter(enabled=True)]


def create_dict(feedback):
    dictionary = {}
    questions = feedback.questions.split(',')
    ratings = feedback.ratings.split(',')
    for i in range(len(questions)):
        dictionary[int(questions[i])] = int(ratings[i])
    return dictionary


def get_question_value(faculty, question):
    total = 0
    itr = 0
    for cfs in ClassFacSub.objects.filter(faculty_id=Faculty.objects.get(name=faculty)):
        for feedback in Feedback.objects.filter(cfs_id=cfs.cfs_id):
            try:
                total += create_dict(feedback)[int(question)]
                itr += 1
            except KeyError:
                continue
    return total/itr if itr != 0 else 0.0


def get_question_number(question, category):
    questions = FdbkQuestions.objects.filter(enabled=True)
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
    total = 0
    itr = 0
    subject = Subject.objects.get(name=subject)
    cfss = ClassFacSub.objects.filter(subject_id=subject)
    for cfs in cfss:
        for feedback in Feedback.objects.filter(cfs_id=cfs.cfs_id):
            total += get_avg_of(feedback)
            itr += 1
    return total/itr if itr != 0 else 0.0


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
    total = 0
    itr = 0
    subject = Subject.objects.get(name=subject)
    cfss = ClassFacSub.objects.filter(subject_id=subject, faculty_id=faculty)
    for cfs in cfss:
        for feedback in Feedback.objects.filter(cfs_id=cfs.cfs_id):
            total += get_avg_of(feedback)
            itr += 1
    return total/itr if itr != 0 else 0.0


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
    cfs = Feedback.objects.all().values_list('cfs_id').distinct()
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
    total = 0
    itr = 0
    for feedback in Feedback.objects.filter(cfs_id=cfs):
        try:
            total += create_dict(feedback)[int(question)]
            itr += 1
        except KeyError:
            continue
    return total/itr if itr != 0 else 0.0


def get_all_timelines(faculty):
    # TODO: check errors
    faculty = Faculty.objects.get(name=faculty)
    cfss = ClassFacSub.objects.filter(faculty_id=faculty)
    timelines = []
    timeline_objs = []
    for cfs in cfss:
        for feedback in Feedback.objects.filter(cfs_id=cfs.cfs_id):
            my_date = feedback.session_id.timestamp.date()
            if my_date in timelines:
                continue
            timelines.append(my_date)
    for cfs in cfss:
        for timeline in timelines:
            summ = 0
            itr = 0
            for feedback in Feedback.objects.filter(cfs_id=cfs.cfs_id):
                if feedback.session_id.timestamp.date() == timeline:
                    ratings = feedback.ratings.split(',')
                    for i in range(len(ratings)):
                        if i in Timeline.get_selected_questions():
                            summ += int(ratings[i])
                            itr += 1
            if itr == 0:
                avg = 0.0
            else:
                avg = summ / itr
            timeline_objs.append(Timeline(timeline, avg))

    return timeline_objs


def get_selected_questions():
    question_list = []
    for q_id in Timeline.get_selected_questions():
        question_list.append(FdbkQuestions.objects.get(question_id=q_id))
    return question_list


def get_sessions_of(class_id):
    sessions = []
    for initiation in get_initiations_of(class_id):
        for session in Session.objects.filter(initiation_id=initiation):
            sessions.append(session)
    return sessions


def get_initiations_of(class_id):
    initiations = []
    for initiation in Initiation.objects.all():
        if initiation.class_id == class_id:
            initiations.append(initiation)
    return initiations
