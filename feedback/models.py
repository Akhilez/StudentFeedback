from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, validate_comma_separated_integer_list
from django.db import models

# Create your models here.
from StudentFeedback.settings import MAX_QUESTIONS


class Classes(models.Model):
    class Meta:
        unique_together = (('year', 'branch', 'section'),)

    class_id = models.AutoField(primary_key=True)
    year = models.IntegerField(
        validators=[MaxValueValidator(4), MinValueValidator(1)] #use IntegerRangeField when admin enters the years
    )
    branch = models.CharField(max_length=10)
    section = models.CharField(max_length=1, null=True)
    no_of_students = models.IntegerField(default=75)

    def __str__(self):
        return str(str(self.year)+" "+str(self.branch)+" "+str(self.section))


class Faculty(models.Model):
    faculty_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Subject(models.Model):
    subject_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class ClassFacSub(models.Model):
    cfs_id = models.AutoField(primary_key=True)
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)
    faculty_id = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    subject_id = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.class_id) +"------------"+ str(self.faculty_id) + "-------------" + str(self.subject_id)


class Student(models.Model):
    hallticket_no = models.CharField(max_length=10, primary_key=True)
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)

    def __str__(self):
        return self.hallticket_no+str(self.class_id)


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


class Attendance(models.Model):
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student)


class Notes(models.Model):
    note_id = models.AutoField(primary_key=True)
    note = models.TextField()

class Category(models.Model):
    category = models.CharField(max_length=30, primary_key=True)

class FdbkQuestions(models.Model):
    question_id = models.AutoField(
        primary_key=True,
        validators=[MaxValueValidator(MAX_QUESTIONS)]
    )
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
    relation_id = models.ForeignKey(ClassFacSub, on_delete=models.CASCADE)

    ratings = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=MAX_QUESTIONS*3
    )

    #ratings = models.CommaSeparatedIntegerField(max_length=20)  #Deprecated way to use it

    '''  #this works only with postgresql
    questions = ArrayField(
        models.IntegerField(validators=[MaxValueValidator(5)]),
        size=MAX_QUESTIONS,
    )
    '''
    '''  #this is a very bad way
    question_1 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_2 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_3 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_4 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_5 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_6 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_7 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_8 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_9 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_10 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_11 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_12 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_13 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_14 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_15 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_16 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_17 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_18 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_19 = models.IntegerField(validators=[MaxValueValidator(5)])
    question_20 = models.IntegerField(validators=[MaxValueValidator(5)])
    '''
    remarks = models.ForeignKey(Notes, on_delete=models.CASCADE, null=True)

