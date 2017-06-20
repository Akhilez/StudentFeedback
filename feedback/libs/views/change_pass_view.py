import re
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from StudentFeedback.settings import CONDUCTOR_GROUP
from feedback.forms import ProfileForm
from feedback.libs.view_helper import feedback_running

__author__ = 'Akhil'


def get_view(request):
    if feedback_running(request):
        return redirect('/feedback/questions/')

    template = 'feedback/changepass.html'
    context = {'conductor_group': CONDUCTOR_GROUP, 'active': 'changepass'}
    if request.method == "POST":
        formset = ProfileForm(request.POST)
        if (formset.is_valid()):
            # formset.save()
            firstname = request.POST.get('firstname', '')
            lastname = request.POST.get('lastname', '')
            newpass = request.POST.get('newpass', '')
            repass = request.POST.get('repass', '')
            email = request.POST.get('email', '')
            password = request.POST.get('password', '')
            if check_password(password, request.user.password):
                if firstname:
                    u = User.objects.get(username=request.user)
                    u.first_name = firstname
                    u.save()
                    context['fir'] = 'notnull'
                if lastname:
                    u = User.objects.get(username=request.user)
                    u.last_name = lastname
                    u.save()
                    context['sec'] = 'notnull'
                if email:
                    u = User.objects.get(username=request.user)
                    u.email = email
                    u.save()
                    context['ec'] = 'notnull'
                if newpass:
                    if repass:
                        if newpass == repass:
                            x = True
                            while x:
                                if (len(newpass) < 6 or len(newpass) > 12):
                                    break
                                elif not re.search("[a-z]", newpass):
                                    break
                                elif not re.search("[0-9]", newpass):
                                    break
                                elif not re.search("[A-Z]", newpass):
                                    break
                                elif re.search("\s", newpass):
                                    break
                                else:
                                    user = request.user
                                    user.set_password(newpass)
                                    user.save()
                                    context['pas'] = 'notnull'
                                    x = False
                                    break
                            if x:
                                context['passnotvalid'] = 'notnull'
                        else:
                            context['repass'] = 'notnull'
            else:
                context['wrongpass'] = 'notnull'
    formset = ProfileForm()
    context['formset'] = formset
    return render(request, template, context)