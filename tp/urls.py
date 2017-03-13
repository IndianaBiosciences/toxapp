""" defines URL patterns for the tp site """

from django.conf.urls import url
from .import views

urlpatterns = [
    # view all experiments
    url(r'^experiments/$', views.ExperimentView.as_view(), name='experiments'),

    # view single experiment detail
    url(r'^experiments/(?P<pk>[0-9]+)$', views.ExperimentDetailView.as_view(), name='experiments-list'),

    # edit single experiment;
    url(r'^experiment/add/$', views.ExperimentCreate.as_view(), name='experiment-add'),
    url(r'^experiment/(?P<pk>[0-9]+)/$', views.ExperimentUpdate.as_view(), name='experiment-update'),
    url(r'^experiment/(?P<pk>[0-9]+)/delete/$', views.ExperimentDelete.as_view(), name='experiment-delete'),

    # upload files containing sample-level data
    url(r'^samples_upload/$', views.UploadSamplesView.as_view(), name='samples-upload'),

    # upload expression dialog
    url(r'^upload_data/$', views.upload_data, name='upload_data'),

    # setup analysis
    url(r'^analyze/$', views.analyze, name='analyze'),
    url(r'^analyze/(?P<pk>\d+)/$', views.analyze, name='analyze'),
]
