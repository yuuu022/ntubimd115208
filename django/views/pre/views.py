from django.contrib import messages
from django.shortcuts import redirect, render

from core.forms import UserProfileForm


def add_user(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User successfully created!')
            return redirect('add_user')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm()

    return render(request, 'add_user.html', {'form': form})
