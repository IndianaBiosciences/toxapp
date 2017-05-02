""" defines URL patterns for the tp site """

from django.conf.urls import url
from .import views

urlpatterns = [

    # view all studies
    url(r'^studies/$', views.StudyView.as_view(), name='studies'),

    # edit single study;
    url(r'^study/add/$', views.StudyCreate.as_view(), name='study-add'),
    url(r'^study/(?P<pk>[0-9]+)/$', views.StudyUpdate.as_view(), name='study-update'),
    url(r'^study/(?P<pk>[0-9]+)/delete/$', views.StudyDelete.as_view(), name='study-delete'),

    # view all experiments
    url(r'^experiments/$', views.ExperimentView.as_view(), name='experiments'),

    # view single experiment detail
    url(r'^experiments/(?P<pk>[0-9]+)$', views.ExperimentDetailView.as_view(), name='experiments-list'),

    # edit single experiment;
    url(r'^experiment/add/$', views.ExperimentCreate.as_view(), name='experiment-add'),
    url(r'^experiment/(?P<pk>[0-9]+)/$', views.ExperimentUpdate.as_view(), name='experiment-update'),
    url(r'^experiment/(?P<pk>[0-9]+)/delete/$', views.ExperimentDelete.as_view(), name='experiment-delete'),

    # confirm / edit existing experiments for association to study
    url(r'^experiments_confirm/$', views.experiments_confirm, name='experiments-confirm'),

    # view all samples
    url(r'^samples/$', views.SampleView.as_view(), name='samples'),

    # edit single sample;
    url(r'^sample/add/$', views.SampleCreate.as_view(), name='sample-add'),
    url(r'^sample/(?P<pk>[0-9]+)/$', views.SampleUpdate.as_view(), name='sample-update'),
    url(r'^sample/(?P<pk>[0-9]+)/delete/$', views.SampleDelete.as_view(), name='sample-delete'),

    # confirm / edit existing samples for association to study
    url(r'^samples_confirm/$', views.samples_confirm, name='samples-confirm'),

    # upload files containing sample-level data
    url(r'^samples_upload/$', views.UploadSamplesView.as_view(), name='samples-upload'),

    # bulk-add and review samples from uploaded file
    url(r'^samples_add/$', views.create_samples, name='samples-add'),

    # associate newly added experiments with newly added samples
    url(r'^experiment_sample_add/(?P<reset>\d+)$', views.create_experiment_sample_pair, name='experiment-sample-reset'),
    url(r'^experiment_sample_add/', views.create_experiment_sample_pair, name='experiment-sample-add'),

    # display the configured experiment vs. sample pairs for group fold change calculation
    url(r'^experiment_sample_confirm/$', views.confirm_experiment_sample_pair, name='experiment-sample-confirm'),

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

    # display list of module scores
    url(r'^analysis_summary/$', views.analysis_summary, name='analysis-summary'),

    # display list of module scores
    url(r'^module_scores/$', views.ModuleFilteredSingleTableView.as_view(), name='module-scores'),

    # display list of module scores
    url(r'^gsa_scores/$', views.GSAFilteredSingleTableView.as_view(), name='gsa-scores'),  # display list of module scores

    # display list of fold-change results at gene level
    url(r'^gene_results/$', views.FoldChangeSingleTableView.as_view(), name='gene-foldchange'),
]
