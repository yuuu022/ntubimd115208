from django.shortcuts import render

def pregnancy_case(request):
    return render(request, 'pregnancycase/pregnancycase.html')

def add_pregnancy_case(request):
    return render(request, 'pregnancycase/add_pregnancy_case.html')



def edit_pregnancy_case(request):
    return render(request, 'pregnancycase/edit_pregnancy_case.html')
