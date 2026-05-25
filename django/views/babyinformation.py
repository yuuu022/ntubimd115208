from django.shortcuts import render

def baby(request):
    return render(request, 'baby/babyinformation.html')

def add_baby_information(request):
    return render(request, 'baby/add_baby_information.html')

def edit_baby_information(request):
    return render(request, 'baby/edit_baby_information.html')

def add_baby_record(request):
    return render(request, 'baby/add_baby_record.html')
