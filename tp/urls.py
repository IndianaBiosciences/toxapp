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

    # confirm / edit experiments for which data will be uploaded
    url(r'^experiments_confirm/$', views.experiments_confirm, name='experiments-confirm'),

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

    # associate newly added experiments with newly added samples
    url(r'^experiment_sample_add/$', views.create_experiment_sample_pair, name='experient-sample-add'),

    # display the configured experiment vs. sample pairs for group fold change calculation
    url(r'^experiment_sample_confirm/$', views.confirm_experiment_sample_pair, name='experient-sample-confirm'),

    # run the python/R process to calculate gene-level fold change values
    url(r'^compute_fold_change/$', views.compute_fold_change, name='compute-fold-change'),

    # upload a delimited file defining identifier vs. entrez gene for the measurement technology
    url(r'^tech_map_upload/$', views.UploadTechMapView.as_view(), name='techmap-upload'),

    # view the experiments in analysis 'cart'
    url(r'^analyze/$', views.analyze, name='analyze'),
    # add an experiment to the analysis 'cart'; not exposing this method on experiment list
    url(r'^analyze/(?P<pk>\d+)/$', views.analyze, name='analyze'),

    #TODO temporary handlers that will need to be replaced with some javascript functionality for clicking on exp list
    # and redirect to the experiments list; will want to avoid this to avoid refreshing page when filtering functionality
    # is built
    url(r'^cart_add/(?P<pk>\d+)/$', views.cart_add, name='cart-add'),
    url(r'^cart_del/(?P<pk>\d+)/$', views.cart_del, name='cart-del'),

]
