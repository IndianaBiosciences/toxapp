""" defines URL patterns for the tp site """

from django.conf.urls import url
from . import views


urlpatterns = [
    # view all experiments
    url(r'^experiments/$', views.experiments, name='experiments'),

    # view to create or edit an entry
    #url(r'^experiment/(?P<experiment_id>\d+)/$', views.experiment, name='experiment'),
    url(r'^experiment/$', views.get_experiment, name='get_experiment'),
]

