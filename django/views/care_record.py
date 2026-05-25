from django.shortcuts import render, redirect

def add_care_reminder(request):
    return render(request, 'index/add_care_reminder.html')
