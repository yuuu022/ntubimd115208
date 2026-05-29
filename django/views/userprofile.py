from django.shortcuts import render, redirect
from views.session_utils import get_current_user_profile

def userprofile(request):
    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')

    return render(request, 'user/userprofile.html', {
        'current_user': current_user,
    })

def edit_userprofile(request):
    current_user = get_current_user_profile(request)
    if not current_user:
        return redirect('login')

    return render(request, 'user/edit_userprofile.html', {
        'current_user': current_user,
    })

def edit_family_member(request):
    return render(request, 'user/edit_family_member.html')
