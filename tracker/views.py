from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from tracker.models import User

def is_logged_in(request):
    if request.session.get('tracker_login', False):
        return True
    else:
        return False

def index(request):
	if is_logged_in(request):
		return HttpResponseRedirect(reverse('tracker:home'))
	else:
		params = {}
		return render(request, 'tracker/index.html', params)

def login(request):
	if is_logged_in(request):
		return HttpResponseRedirect(reverse('tracker:home'))
	else:
		try:
		    params = dict(request.session['tracker_login_params'])
		    del request.session['tracker_login_params']
		except KeyError:
		    params = {}
		return render(request, 'tracker/login.html',params)

def authenticate(request):
	if 'username' in request.POST:
		username = request.POST['username']
		password = request.POST['password']
		try:
		    euser = User.objects.get(username=username, password=password)
		except User.DoesNotExist:
		    return goto_login_page(request, {'msg':'Login Incorrect'})
		if euser.active == True:
			request.session.set_expiry(3600)
			request.session['tracker_login'] = True
			request.session['tracker_user_id'] = euser.pk
			request.session['tracker_username'] = username
			request.session['tracker_handles'] = list(euser.handle.values())
			return HttpResponseRedirect(reverse('tracker:home'))
		else:
			return goto_login_page(request, {'msg':'User Inactive'})
	else:
		try:
		    params = dict(request.session['tracker_login_params'])
		    del request.session['tracker_login_params']
		except KeyError:
		    params = {}
		return goto_login_page(request, params)

def home(request):
	if is_logged_in(request):
		username = request.session['tracker_username']
		handles = request.session['tracker_handles']
		return render(request, 'tracker/home.html',{'username':username,
												'handles':handles})
	else:
		return HttpResponseRedirect(reverse('tracker:login'))

def goto_login_page(request, params):
    request.session['tracker_login_params'] = params
    return HttpResponseRedirect(reverse('tracker:login'))

def logout(request):
	if is_logged_in(request):
		"Delete all session variables."
		session_keys = [key for key in request.session.keys() if key.startswith('tracker_')]

		for sk in session_keys:
		    del request.session[sk]
		msg = "You Have Logged Out"
		return goto_login_page(request, {'msg':msg})
	else:
	    return HttpResponseRedirect(reverse('tracker:login'))