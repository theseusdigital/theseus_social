from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from tracker.models import User
from tracker import views

def index(request):
	if views.is_logged_in(request):
		users = User.objects.all()
		print users
		return render(request, 'tracker/trackmodule/index.html', {'users':users})
	else:
		return HttpResponseRedirect(reverse('tracker:login'))