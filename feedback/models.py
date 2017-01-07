from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# Create your models here.


class Classes(models.Model):
    class_id = models.IntegerField(primary_key=True)
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
    relation_id = models.IntegerField(primary_key=True)
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)
    faculty_id = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    subject_id = models.ForeignKey(Subject, on_delete=models.CASCADE)

