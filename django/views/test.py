from django.shortcuts import render, redirect
from django.contrib import messages
from core.forms import UserProfileForm
from views.baby_growthmap import baby_growthmap



def add_user(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'User successfully created!')
                return redirect('add_user')
            except Exception as e:
                messages.error(request, f'Error creating user: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm()

    return render(request, 'add_user.html', {'form': form})
