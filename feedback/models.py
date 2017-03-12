from django.contrib.auth.models import User, Group
from django.core.validators import MinValueValidator, MaxValueValidator, validate_comma_separated_integer_list
from django.db import models
from django.dispatch import receiver


# Create your models here.
from django.db.models.signals import post_save, pre_save
from StudentFeedback.settings import MAX_QUESTIONS


class Classes(models.Model):
    class Meta:
        db_table = 'classes'
        unique_together = (('year', 'branch', 'section'),)

    class_id = models.AutoField(primary_key=True)
    year = models.IntegerField(
        validators=[MaxValueValidator(4), MinValueValidator(1)] #use IntegerRangeField when admin enters the years
    )
    branch = models.CharField(max_length=10)
    section = models.CharField(max_length=1, null=True)
    no_of_students = models.IntegerField(default=75)

    def __str__(self):
        yearDict = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}
        if self.section is None:
            sec = ""
        else:
            sec = str(self.section)
        return str(yearDict[self.year]+" "+str(self.branch)+" "+sec)


class Faculty(models.Model):
    faculty_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'faculty'


class Subject(models.Model):
    subject_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'subject'


class ClassFacSub(models.Model):
    cfs_id = models.AutoField(primary_key=True)
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)
    faculty_id = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    subject_id = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.class_id) +"------------"+ str(self.faculty_id) + "-------------" + str(self.subject_id)

    class Meta:
        db_table = 'classFacSub'
        unique_together = (('class_id', 'faculty_id', 'subject_id'),)


class Student(models.Model):
    hallticket_no = models.CharField(max_length=10, primary_key=True)
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)

    def __str__(self):
        return self.hallticket_no+" --- "+str(self.class_id)

    class Meta:
        db_table = 'student'


class Initiation(models.Model):
    initiation_id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)


class Session(models.Model):
    session_id = models.CharField(max_length=5, primary_key=True)
    timestamp = models.DateTimeField()
    initiation_id = models.ForeignKey(Initiation, on_delete=models.CASCADE)
    taken_by = models.ForeignKey(User, on_delete=models.CASCADE)
    master = models.BooleanField(default=False)
    stutimeout = models.IntegerField(default=5)
    mastersession = models.CharField(max_length=5, null=True)#references master session


class Attendance(models.Model):
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student)


class Notes(models.Model):
    note_id = models.AutoField(primary_key=True)
    note = models.TextField()
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE, null=True)


class Category(models.Model):
    category = models.CharField(max_length=30, primary_key=True)


class FdbkQuestions(models.Model):
    question_id = models.AutoField(primary_key=True)
    question = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.CharField(max_length=30, null=True)


class Config(models.Model):
    key = models.CharField(max_length=20)
    value = models.CharField(max_length=20)
    description = models.TextField()


class Feedback(models.Model):
    class Meta:
        unique_together = (('session_id', 'student_no', 'relation_id', 'category'),)
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    student_no = models.IntegerField()
    relation_id = models.CharField(null=True, max_length=25)

    ratings = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=MAX_QUESTIONS*4
    )

def create_branch_group(sender, **kwargs):
        allBranches = []
        branchesQlist = Classes.objects.values_list('branch').distinct()
        for branch in branchesQlist:
            allBranches.append(branch[0])
        currentBranch = kwargs['instance'].branch
        if currentBranch not in allBranches:
            try:
                Group.objects.create(name=currentBranch)
            except:
                pass

pre_save.connect(create_branch_group, sender=Classes)



class LOAquestions(models.Model):
    question_id = models.AutoField(primary_key=True)
    question = models.TextField()
    subject_id=models.ForeignKey(Subject,on_delete=models.CASCADE)

class FeedbackLoa(models.Model):
    class Meta:
        unique_together = (('session_id', 'student_no', 'relation_id'),)
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    student_no = models.IntegerField()
    relation_id = models.CharField(null=True, max_length=25)

    loaratings = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=MAX_QUESTIONS*4

    )

class User_Otp(models.Model):
    Userid = models.ForeignKey(User, on_delete=models.CASCADE,)
    otp = models.IntegerField()


