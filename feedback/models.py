from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator, validate_comma_separated_integer_list
from django.db import models

# Create your models here.


MAX_QUESTIONS = 20


class Classes(models.Model):
    class_id = models.AutoField(primary_key=True)
    year = models.IntegerField(
        validators=[MaxValueValidator(4), MinValueValidator(1)] #use IntegerRangeField when admin enters the years
    )
    branch = models.CharField(max_length=10)
    section = models.CharField(max_length=1)


class Faculty(models.Model):
    faculty_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)


class Subject(models.Model):
    subject_id = models.CharField(max_length=6)
    name = models.CharField(max_length=200)


class ClassFacSub(models.Model):
    relation_id = models.AutoField(primary_key=True)
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)
    faculty_id = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    subject_id = models.ForeignKey(Subject, on_delete=models.CASCADE)


class Student(models.Model):
    hallticket_no = models.CharField(max_length=10, primary_key=True)
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)


class Initiation(models.Model):
    initiation_id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)


class Session(models.Model):
    session_id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    initiation_id = models.ForeignKey(Initiation, on_delete=models.CASCADE)
    taken_by = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=5, unique=True)


class Attendance(models.Model):
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student)
    mac_address = models.GenericIPAddressField()#models.CharField(max_length=20)


class Notes(models.Model):
    note_id = models.AutoField(primary_key=True)
    note = models.TextField()


class FdbkQuestions(models.Model):
    question_id = models.AutoField(primary_key=True, validators=[MaxValueValidator(MAX_QUESTIONS), MinValueValidator(1)])
    question = models.TextField()


class Feedback(models.Model):
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    relation_id = models.ForeignKey(ClassFacSub, on_delete=models.CASCADE)

    ratings = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=MAX_QUESTIONS**2-1
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
    remarks = models.ForeignKey(Notes, on_delete=models.CASCADE)
    #idk = models.ForeignKey(Notes, on_delete=models.CASCADE)
