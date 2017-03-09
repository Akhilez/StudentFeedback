from django import forms
from feedback.models import Student



class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(max_length=20, widget=forms.PasswordInput)

class ProfileForm(forms.Form):
    firstname = forms.CharField(max_length=100, required=False)
    lastname = forms.CharField(max_length=100, required=False)
    email = forms.CharField(max_length=100, required=False)
    newpass = forms.CharField(max_length=100, required=False, widget=forms.PasswordInput)
    repass = forms.CharField(max_length=100, required=False, widget=forms.PasswordInput)
    password = forms.CharField(max_length=100, widget=forms.PasswordInput)