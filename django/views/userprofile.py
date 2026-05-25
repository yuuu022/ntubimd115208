from django.shortcuts import render

def userprofile(request):
    return render(request, 'user/userprofile.html')

def edit_userprofile(request):
    return render(request, 'user/edit_userprofile.html')

def edit_family_member(request):
    return render(request, 'user/edit_family_member.html')
