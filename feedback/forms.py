from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=20, widget=forms.PasswordInput)

class InitiateForm(forms.Form):
    user = forms.CharField(max_length=100)