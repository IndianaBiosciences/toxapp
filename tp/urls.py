""" defines URL patterns for the tp site """

from django.conf.urls import url
from . import views


urlpatterns = [
    # view all experiments
    url(r'^experiments/$', views.experiments, name='experiments'),

    # view single experiment; if no experiment id given then create one in the view
    url(r'^experiment/$', views.experiment, name='experiment'),
    url(r'^experiment/(?P<experiment_id>\d+)/$', views.experiment, name='experiment'),

    # upload expression dialog
    url(r'^upload_data/$', views.upload_data, name='upload_data'),

    # setup analysis
    url(r'^analyze/$', views.analyze, name='analyze'),
    url(r'^analyze/(?P<experiment_id>\d+)/$', views.analyze, name='analyze'),
]

