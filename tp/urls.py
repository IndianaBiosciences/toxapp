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

    # view all samples
    url(r'^samples/$', views.SampleView.as_view(), name='samples'),

    # edit single sample;
    url(r'^sample/add/$', views.SampleCreate.as_view(), name='sample-add'),
    url(r'^sample/(?P<pk>[0-9]+)/$', views.SampleUpdate.as_view(), name='sample-update'),
    url(r'^sample/(?P<pk>[0-9]+)/delete/$', views.SampleDelete.as_view(), name='sample-delete'),

    # upload files containing sample-level data
    url(r'^samples_upload/$', views.UploadSamplesView.as_view(), name='samples-upload'),

    # bulk-add and review samples from uploaded file
    url(r'^samples_add/$', views.create_samples, name='samples-add'),

    # upload expression dialog
    url(r'^upload_data/$', views.upload_data, name='upload_data'),

    # setup analysis
    url(r'^analyze/$', views.analyze, name='analyze'),
    url(r'^analyze/(?P<pk>\d+)/$', views.analyze, name='analyze'),
]
