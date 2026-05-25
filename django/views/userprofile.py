from django.shortcuts import render

def userprofile(request):
    return render(request, 'user/userprofile.html')

def edit_userprofile(request):
    return render(request, 'user/edit_userprofile.html')
