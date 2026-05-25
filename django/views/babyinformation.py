from django.shortcuts import render

def baby(request):
    return render(request, 'baby/babyinformation.html')

def add_baby_profile(request):
    return render(request, 'baby/add_baby_profile.html')

def add_baby_record(request):
    return render(request, 'baby/add_baby_record.html')
