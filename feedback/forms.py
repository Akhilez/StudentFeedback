from django import forms
from feedback.models import Student



class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=20, widget=forms.PasswordInput)

class StudForm(forms.Form):
    studid = forms.CharField(max_length=100)