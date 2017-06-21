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
    sections = Classes.objects.filter(year=int(deformatter[year]), branch=branch).values_list('section').order_by(
        'branch').distinct()
    return [x[0] for x in sections]


def create_Dic(feedback):
    dictionary = {}
    questions = feedback.questions.split(',')
    ratings = feedback.ratings.split(',')
    for i in range(len(questions)):
        if len(questions[i]) == 0 or len(ratings[i]) == 0:
            continue
        dictionary[int(questions[i])] = int(ratings[i])
    return dictionary


def get_avg_of(feedback):
    total = 0
    itr = 0
    my_dict = create_Dic(feedback)
    for question in LOAquestions.objects.filter(enabled=True):
        try:
            total += my_dict[question.question_id]
            itr += 1
        except KeyError:
            continue
    return total / itr if itr != 0 else 0.0


def get_year_value(year):
    classes = Classes.objects.filter(year=deformatter[year])
    total = 0
    itr = 0
    for cls in classes:
        initiations = Initiation.objects.filter(class_id=cls)
        for initiation in initiations:
            sessions = Session.objects.filter(initiation_id=initiation)
            for session in sessions:
                feedbacks = FeedbackLoa.objects.filter(session_id=session)
                for feedback in feedbacks:
                    total += get_avg_of(feedback)
                    itr += 1
    return total / itr if itr != 0 else 0.0


def get_branch_value(year, branch):
    classes = Classes.objects.filter(year=deformatter[year], branch=branch)
    total = 0
    itr = 0
    for cls in classes:
        initiations = Initiation.objects.filter(class_id=cls)
        for initiation in initiations:
            sessions = Session.objects.filter(initiation_id=initiation)
            for session in sessions:
                feedbacks = FeedbackLoa.objects.filter(session_id=session)
                for feedback in feedbacks:
                    total += get_avg_of(feedback)
                    itr += 1
    return total / itr if itr != 0 else 0.0


def get_section_value(year, branch, section):
    classes = Classes.objects.filter(year=deformatter[year], branch=branch, section=section)
    total = 0
    itr = 0
    for cls in classes:
        initiations = Initiation.objects.filter(class_id=cls)
        for initiation in initiations:
            sessions = Session.objects.filter(initiation_id=initiation)
            for session in sessions:
                feedbacks = FeedbackLoa.objects.filter(session_id=session)
                for feedback in feedbacks:
                    total += get_avg_of(feedback)
                    itr += 1
    return total / itr if itr != 0 else 0.0


def get_all_subjects():  # not used @akhil
    subjects = Subject.objects.all().values_list('name')
    return [subject[0] for subject in subjects]


def get_all_year_branches():
    return Classes.objects.values_list('year', 'branch')


def get_all_year_sections():
    return Classes.objects.values_list('year', 'branch', 'section')


def get_all_subjects_all_years():
    subjects = Subject.objects.all()
    subjects = [subject.name for subject in subjects]
    subjects.sort()
    return subjects


def get_subjects_in_feedback():  # Ravi
    subject_list = []
    subject = [x[0] for x in FeedbackLoa.objects.all().values_list("subject_id").distinct()]

    for sub in Subject.objects.all():
        if sub.subject_id in subject:
            subject_list.append(sub)

    return subject_list


def get_subject_value_for(subject, class_id):  # done

    total = 0
    itr = 0
    subject = Subject.objects.filter(name=subject)
    for ini in Initiation.objects.filter(class_id=class_id):
        for see in Session.objects.filter(initiation_id=ini):
            for Feed in FeedbackLoa.objects.filter(session_id=see, subject_id=subject):
                total += get_avg_of(Feed)
                itr += 1
    return total / itr if itr != 0 else 0.0


def get_sections_for_subject(subject):
    subject = Subject.objects.get(name=subject)

    cfss = ClassFacSub.objects.filter(subject_id=subject).values_list('class_id').distinct()
    cfss = [x[0] for x in cfss]
    sections = []
    for cfs in cfss:
        sections.append(Classes.objects.get(class_id=cfs).class_id)  # changed to class id
    return sections


def get_feedback_sections_subject(subject):
    sid = Subject.objects.filter(name=subject)
    sess = FeedbackLoa.objects.filter(subject_id=sid).values_list('session_id').distinct()
    classlist = []
    sess = [x[0] for x in sess]
    for s in sess:
        sesid = Session.objects.get(session_id=s)
        classid = sesid.initiation_id.class_id
        classlist.append(classid)
    return classlist


def get_sections_value_for_subject(subject, section):  # code,getting section bars value,for particular sub @ravi
    sid = Subject.objects.filter(name=subject)
    classes = Classes.objects.filter(class_id=section)
    sum = 0
    itr = 0
    for cls in classes:
        initiations = Initiation.objects.filter(class_id=cls)
        for initiation in initiations:
            sessions = Session.objects.filter(initiation_id=initiation)
            for session in sessions:
                feedbacks = FeedbackLoa.objects.filter(session_id=session, subject_id=sid)
                for feedback in feedbacks:
                    ratings = feedback.ratings.split(',')
                    for rating in ratings:
                        if rating == '':
                            continue
                        sum += int(rating)
                        itr += 1
    if itr != 0:
        avg = sum / itr
    else:
        avg = 0.0
    return avg


def get_subjects(year, branch):
    classes = Classes.objects.filter(year=int(deformatter[year]), branch=branch)
    cfs = ClassFacSub.objects.all()
    subjects = []
    for cls in classes:
        subs = cfs.filter(class_id=cls)
        for sub in subs:
            sub_name = sub.subject_id.name
            if sub_name not in subjects:
                subjects.append(sub_name)
    return subjects


def get_subject_value(subject):
    total = 0
    itr = 0
    for feedback in FeedbackLoa.objects.filter(subject_id=subject):
        total += get_avg_of(feedback)
        itr += 1
    return total / itr if itr != 0 else 0.0


