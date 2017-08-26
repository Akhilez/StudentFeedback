import csv
import datetime
import re

from analytics.libs import db_helper
from feedback.models import *


__author__ = 'Akhil'


def is_unassigned(year, branch, classes):
    pattern = year + ',' + branch + ',*'
    for cls in classes:
        if re.search(pattern, cls):
            return True
    return False


def update_classes():
    file = open('externals/student-class.csv', 'r')
    lines = file.readlines()
    now = datetime.datetime.today()
    classes = set()
    for line in lines:
        fields = line.split(',')
        branch = fields[1].strip()
        if branch == '':
            continue
        year = str(int(now.year) - int('20' + fields[0][0] + fields[0][1]))
        section = fields[2].strip()
        if section == '' and is_unassigned(year, branch, classes):
            continue
        classes.add(year + ',' + branch + ',' + section)

    sem = Sem.objects.get(sem_id=1)
    for cls in classes:
        lst = cls.split(',')
        try:
            Classes.objects.create(year=lst[0], branch=lst[1], section=lst[2], sem=sem)

        except:
            pass
    file.close()
    return classes


def update_students():
    file = open('externals/student-class.csv', 'r')
    lines = file.readlines()
    now = datetime.datetime.today()
    classes = set()
    for line in lines:
        fields = line.split(',')
        student = fields[0].strip()
        branch = fields[1].strip()
        if branch == '':
            continue
        year = str(int(now.year) - int('20' + fields[0][0] + fields[0][1]))
        section = fields[2].strip()
        if section == '' and is_unassigned(year, branch, classes):
            continue

        try:
            cls = Classes.objects.get(year=year, branch=branch, section=section)
            Student.objects.create(hallticket_no=student, class_id=cls)
            classes.add(student)
        except:
            try:
                stu = Student.objects.get(hallticket_no=student)
                stu.class_id = Classes.objects.get(year=year, branch=branch, section=section)
            except:
                pass

    file.close()
    return classes


def update_faculty():
    file = open('externals/class-faculty-subject.csv', 'r')
    lines = file.readlines()
    faculty = set()
    for line in lines:
        fields = line.split(',')
        faculty.add(fields[1].strip())

    for fac in faculty:
        try:
            Faculty.objects.create(name=fac)
        except:
            pass

    file.close()
    return faculty


def update_subjects():
    file = open('externals/class-faculty-subject.csv', 'r')
    lines = file.readlines()
    file.close()
    subjects = set()
    for line in lines:
        fields = line.split(',')
        subjects.add(fields[2].strip())

    for subject in subjects:
        try:
            Subject.objects.create(name=subject)
        except:
            pass

    return subjects


def update_class_fac_sub():
    file = open('externals/class-faculty-subject.csv', 'r')
    lines = file.readlines()
    file.close()
    relations = set()
    for line in lines:
        fields = line.split(',')
        cls = fields[0].split('-')
        branch = cls[0].strip()
        section = cls[1].strip()
        year = cls[2].strip()[0]
        faculty = fields[1].strip()
        subject = fields[2].strip()
        relations.add(year + '-|-' + branch + '-|-' + section + '-|-' + faculty + '-|-' + subject)
    for relation in relations:
        params = relation.split('-|-')
        try:
            cls = Classes.objects.get(year=params[0], branch=params[1], section=params[2])
            faculty = Faculty.objects.get(name=params[3])
            subject = Subject.objects.get(name=params[4])
            ClassFacSub.objects.create(class_id=cls, faculty_id=faculty, subject_id=subject)
        except:
            pass

    return relations


def update_faculty_questions():
    file = open('externals/faculty-questions.csv', 'r')
    lines = file.readlines()
    file.close()
    questions = set()
    for line in lines:
        fields = line.split(',')
        question = fields[0].strip()
        subcategory = fields[1].strip()
        try:
            FdbkQuestions.objects.get(question=question, subcategory=subcategory)
            continue
        except:
            FdbkQuestions.objects.create(question=question, subcategory=subcategory)
            questions.add(question + '\t' + subcategory)

    return questions


def update_loa_questions():
    op = []
    with open("externals/loa-questions.csv") as file:
        reader = csv.reader(file)
        for row in reader:
            op.append(row)
    file.close()

    for row in op:
        subject = Subject.objects.filter(name=row[1])[0]
        LOAquestions.objects.create(question=row[0], subject_id=subject)

    return op


def update_faculty_names(confirm=False):
    faculty_changes = []
    with open("externals/faculty_name_updates.csv") as file:
        reader = csv.reader(file)
        i = 1
        for row in reader:
            try:
                prev_name = row[0]
                new_name = row[1]
                faculty = Faculty.objects.get(name=prev_name)
                faculty_changes.append(str(i)+". " + str(faculty) + ' ==== ' + str(new_name))
                if confirm:
                    faculty.name = new_name
                    faculty.save()
                i += 1
            except:
                pass

    return faculty_changes


def update_cfs_names(confirm=False):
    cfs_changes = []
    with open("externals/cfs_updates.csv") as file:
        reader = csv.reader(file)
        i = 1
        for row in reader:
            #try:
                prev_class = get_class_for(row[0])
                prev_subject = Subject.objects.get(name=row[1])
                prev_faculty = Faculty.objects.get(name=row[2])
                new_faculty = Faculty.objects.get(name=row[3])
                cfs = ClassFacSub.objects.get(class_id=prev_class, faculty_id=prev_faculty,
                                              subject_id=prev_subject)
                cfs_changes.append(
                    str(i)+") "+str(prev_class)+" - "+str(prev_subject)+" - "+str(prev_faculty)+" - "+str(new_faculty))
                if confirm:
                    cfs.faculty_id = new_faculty
                    cfs.save()
                i += 1
            #except:
                #pass
    return cfs_changes


def get_class_for(class_name):
    for classes in Classes.objects.all():
        if str(classes) == class_name:
            return classes
    return None
