from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def profile(request):
	return render(request, 'custom_auth/profile.html')

@login_required
def password_change(request):
	return render(request, 'custom_auth/password_change_form.html')

@login_required
def password_change_done(request):
	return render(request, 'custom_auth/password_change_done.html')
