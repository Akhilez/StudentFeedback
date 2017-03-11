from django import forms
from feedback.models import Student



class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(max_length=20, widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

class ProfileForm(forms.Form):
    firstname = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    lastname = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    newpass = forms.CharField(max_length=100, required=False, widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}))
    repass = forms.CharField(max_length=100, required=False, widget=forms.PasswordInput(attrs={'placeholder': 'Re-Enter Password'}))
    password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'placeholder': 'Current Password'}))

class PasswordResetRequestForm(forms.Form):
    email_or_username = forms.CharField(label=("Email Or Username"), max_length=254)