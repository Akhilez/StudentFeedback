from django.contrib import admin
from feedback.models import *

# Register your models here.

admin.site.site_header = "Administration"


admin.site.register(Sem)
admin.site.register(Classes)
admin.site.register(Subject)
admin.site.register(Faculty)
admin.site.register(ClassFacSub)
admin.site.register(Student)
admin.site.register(Config)
