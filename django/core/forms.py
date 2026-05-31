from django import forms
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['line_name', 'avatar', 'email', 'password', 'birthday']
        widgets = {
            'line_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter your Line Name'}),
            'avatar': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Avatar URL'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Enter your email'}),
            'birthday': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }
