from django.conf.urls import url

from tracker.trackmodule import views

app_name = 'tracker'
urlpatterns = [
    url(r'^$', views.index, name='index')
]