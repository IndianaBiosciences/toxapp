""" defines URL patterns for the tp site """

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from .import views

app_name = "tp"

urlpatterns = [

    # view all studies
    url(r'^studies/$', login_required(views.StudyView.as_view()), name='studies'),

    # edit single study;
    url(r'^study/add/$', login_required(views.StudyCreate.as_view()), name='study-add'),
    url(r'^study/(?P<pk>[0-9]+)/$', login_required(views.StudyUpdate.as_view()), name='study-update'),
    url(r'^study/(?P<pk>[0-9]+)/delete/$', login_required(views.StudyDelete.as_view()), name='study-delete'),

    # view all experiments
    url(r'^experiments/$', login_required(views.ExperimentView.as_view()), name='experiments'),
    # view all experiments for a given study ID
    url(r'^experiments/(?P<study>\d+)$', login_required(views.ExperimentView.as_view()), name='experiments-bystudy'),

    # view single experiment detail
    url(r'^experiments/(?P<pk>[0-9]+)$', login_required(views.ExperimentDetailView.as_view()), name='experiments-list'),

    # edit single experiment;
    url(r'^experiment/add/$', login_required(views.ExperimentCreate.as_view()), name='experiment-add'),
    url(r'^experiment/(?P<pk>[0-9]+)/$', login_required(views.ExperimentUpdate.as_view()), name='experiment-update'),
    url(r'^experiment/(?P<pk>[0-9]+)/delete/$', login_required(views.ExperimentDelete.as_view()), name='experiment-delete'),

    # confirm / edit existing experiments for association to study
    url(r'^experiments_confirm/$', login_required(views.experiments_confirm), name='experiments-confirm'),

    # view all samples
    url(r'^samples/$', login_required(views.SampleView.as_view()), name='samples'),

    # edit single sample;
    url(r'^sample/add/$', login_required(views.SampleCreate.as_view()), name='sample-add'),
    url(r'^sample/(?P<pk>[0-9]+)/$', login_required(views.SampleUpdate.as_view()), name='sample-update'),
    url(r'^sample/(?P<pk>[0-9]+)/delete/$', login_required(views.SampleDelete.as_view()), name='sample-delete'),

    # confirm / edit existing samples for association to study
    url(r'^samples_confirm/$', login_required(views.samples_confirm), name='samples-confirm'),

    # upload files containing sample-level data
    url(r'^samples_upload/$', login_required(views.UploadSamplesView.as_view()), name='samples-upload'),

    # bulk-add and review samples from uploaded file
    url(r'^samples_add/$', login_required(views.create_samples), name='samples-add'),

    # associate newly added experiments with newly added samples
    url(r'^experiment_sample_add/(?P<reset>\w+)$', login_required(views.create_experiment_sample_pair), name='experiment-sample-reset'),
    url(r'^experiment_sample_add/', login_required(views.create_experiment_sample_pair), name='experiment-sample-add'),

    # display the configured experiment vs. sample pairs for group fold change calculation
    url(r'^experiment_sample_confirm/$', login_required(views.confirm_experiment_sample_pair), name='experiment-sample-confirm'),

    # run the python/R process to calculate gene-level fold change values
    url(r'^compute_fold_change/$', login_required(views.compute_fold_change), name='compute-fold-change'),

    # upload a delimited file defining identifier vs. entrez gene for the measurement technology
    url(r'^tech_map_upload/$', login_required(views.UploadTechMapView.as_view()), name='techmap-upload'),

    # view the experiments in analysis 'cart'
    url(r'^cart_edit/$', views.cart_edit, name='cart-edit'),
    # add an experiment to the analysis 'cart'; not exposing this method on experiment list
    url(r'^cart_edit/(?P<pk>\d+)/$', views.cart_edit, name='cart-edit'),

    url(r'^cart_add/(?P<pk>\d+)/$', views.cart_add, name='cart-add'),
    url(r'^cart_del/(?P<pk>\d+)/$', views.cart_del, name='cart-del'),
    url(r'^cart_empty/$', views.cart_empty, name='cart-empty'),
    url(r'^cart_add_all/$', views.cart_add_all, name='cart-add-all'),
    url(r'^cart_add_filtered/$', views.cart_add_filtered, name='cart-add-filtered'),

    # here, a feature means a gene expression 'feature' - module, geneset, gene
    url(r'^feature_add/(?P<pk>\d+)/(?P<ftype>\w+)/$', views.feature_add, name='feature-add'),
    url(r'^feature_del/(?P<pk>\d+)/(?P<ftype>\w+)/$', views.feature_del, name='feature-del'),
    url(r'^feature_empty/$', views.feature_empty, name='feature-empty'),
    url(r'^feature_add_filtered/$', views.feature_add_filtered, name='feature-add-filtered'),
    url(r'^manage_features/(?P<ftype>\w+)/$', views.manage_features, name='manage-features'),

    # display overview of results for selected experiments
    url(r'^analysis_summary/$', login_required(views.analysis_summary), name='analysis-summary'),

    # display list of module scores
    url(r'^module_scores/$', login_required(views.ModuleFilteredSingleTableView.as_view()), name='module-scores'),

    # display list of module scores
    url(r'^gsa_scores/$', login_required(views.GSAFilteredSingleTableView.as_view()), name='gsa-scores'),  # display list of module scores

    # display list of fold-change results at gene level
    url(r'^gene_results/$', login_required(views.FoldChangeSingleTableView.as_view()), name='gene-foldchange'),

    # display list of fold-change results at gene level
    url(r'^similar_experiments/$', login_required(views.SimilarExperimentsSingleTableView.as_view()), name='similar-exps'),

    # display list of toxicology results (clinchem, histo)
    url(r'^toxicology_results/$', login_required(views.ToxicologyResultsSingleTableView.as_view()), name='toxicology-results'),

    # display list of BMD pathway results
    url(r'^bmd_pathway_results/$', login_required(views.BMDPathwayResultsSingleTableView.as_view()),name='bmdpathway-results'),

    # export to excel handler
    url(r'^export_results/(?P<restype>\w+)$', views.export_result_xls, name='export-result'),

    # export filtered results to excel
    url(r'^export_filtered_results/$', views.export_result_xls, name='export-filtered-result'),

    # export filtered results to json for heatmap
    url(r'^heatmap_json/$', views.export_heatmap_json, name='heatmap-json'),

    # export filtered results to json for mapchart
    url(r'^mapchart_json/$', views.export_mapchart_json, name='mapchart-json'),

    # export filtered results to json for barchart
    url(r'^barchart_json/$', views.export_barchart_json, name='barchart-json'),

    # export filtered results to json for treemap
    url(r'^treemap_json/$', views.export_treemap_json, name='treemap-json'),

    url(r'^get_tox_assoc/$', login_required(views.ToxAssociation.as_view()), name='get-tox-assoc'),

    url(r'^get_feature_subset/(?P<geneset_id>\d+)$', views.get_feature_subset, name='get-feature-subset'),

    url(r'^manage_session/$', views.manage_session, name='manage-session'),

    url(r'^gene_detail/(?P<gene_id>\d+)$', views.gene_detail, name='gene-detail'),

    # prepare a CSV file with unique ID that Leiden can pull in for their human primary heps analysis
    url(r'^export_leiden/$', views.export_leiden, name='export-leiden'),

]
