from django.conf.urls import include, url

from tracker import views

app_name = 'tracker'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.login, name='login'),
    url(r'^authenticate/$', views.authenticate, name='authenticate'),
    url(r'^home/$', views.home, name='home'),
    url(r'^logout/$', views.logout, name='logout'),

    url(r'^trackmodule/', include('tracker.trackmodule.urls', namespace='trackmodule')),
]