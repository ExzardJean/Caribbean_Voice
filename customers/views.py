
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Customer
from .forms import UserProfileForm
from inventory.models import User


def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'customers/list.html', {'customers': customers})

# Vue profil utilisateur connecté
@login_required
def profile_view(request):
    user = request.user
    if not isinstance(user, User):
        user = User.objects.get(pk=user.pk)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            profile = form.save(commit=False)
            pwd1 = form.cleaned_data.get('password1')
            if pwd1:
                profile.set_password(pwd1)
            if 'profile_image' in request.FILES:
                profile.profile_image = request.FILES['profile_image']
            profile.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
    return render(request, 'customers/profile.html', {'form': form})
