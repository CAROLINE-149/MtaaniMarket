# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User  # or Profile if using default User

class SignupForm(UserCreationForm):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User 
        fields = ['username', 'email', 'password1', 'password2', 'role']
