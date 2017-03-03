""" defines URL patterns for the tp site """

from django.conf.urls import url
from . import views


urlpatterns = [
    # view all experiments
    url(r'^experiments/$', views.experiments, name='experiments'),

    # view single experiment
    url(r'^new_experiment/$', views.new_experiment, name='new_experiment'),

    # view single experiment
    url(r'^upload_data/$', views.upload_data, name='upload_data'),
]

