from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Profile
from .forms import ProfileForm

@login_required
def profile_manage_view(request):
    try:
        profile = request.user.profile
        is_update = True
    except Profile.DoesNotExist:
        profile = None
        is_update = False

    if request.method == 'POST':
        if 'delete' in request.POST:
            if profile:
                profile.delete()
                messages.success(request, "Profile deleted successfully.")
            else:
                messages.error(request, "No profile found to delete.")
            return redirect('accounts:profile')

        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            new_profile = form.save(commit=False)
            new_profile.user = request.user
            new_profile.save()
            if is_update:
                messages.success(request, "Profile updated successfully.")
            else:
                messages.success(request, "Profile created successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "There was an error saving the profile. Please check the form.")
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'account/profile.html', {
        'form': form,
        'profile': profile,
        'is_update': is_update,
    })
