from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserProfileForm

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
    
    return render(request, 'core/add_user.html', {'form': form})


#成長地圖畫面
def history(request):
    return render(request, 'core/history.html')
