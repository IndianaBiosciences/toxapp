from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.core.files.storage import FileSystemStorage
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django_tables2 import SingleTableView
from tempfile import gettempdir
from .models import Study, Experiment, Sample, ExperimentSample, FoldChangeResult, ModuleScores, GSAScores,\
                    ExperimentCorrelation, ToxicologyResult
from .forms import StudyForm, ExperimentForm, SampleForm, SampleFormSet, FilesForm, ExperimentSampleForm,\
                   ExperimentConfirmForm, SampleConfirmForm, MapFileForm
from .tasks import load_measurement_tech_gene_map, process_user_files
import tp.filters
import tp.tables

import os
import time
import logging
import csv
import pprint, json
import xlwt

logger = logging.getLogger(__name__)

def index(request):
    """ the home page for tp """
    return render(request, 'index.html')


def get_study_from_session(session):

    studyobj = None
    if session.get('adding_study', None) is None:
        logger.error('no adding_study key in session')
    else:
        try:
            studyobj = Study.objects.get(pk=session['adding_study']['id'])
        except:
            logger.error('study ID stored in session is not valid')

    return studyobj


def reset_session(session):
    """ helper function to restore various session vars used for tracking between views """

    logger.debug('Resetting session info for tracking metadata across handlers')
    # TODO - delete the existing tmp_dir first
    # delete and not set to None due to manner in which they are created as lists
    for attr in ['tmp_dir', 'last_exp_id', 'computation_recs', 'computation_config', 'adding_study', 'added_sample_names', 'sample_file', 'sim_list']:
        try:
            del session[attr]
        except KeyError:
            pass


def get_temp_dir(obj):

    if obj.request.session.get('tmp_dir', None) is None:
        tmp = os.path.join(gettempdir(), '{}'.format(hash(time.time())))
        os.makedirs(tmp)
        os.chmod(tmp, 0o777)
        logger.debug('Creating temporary working directory %s', tmp)
        obj.request.session['tmp_dir'] = tmp

    return obj.request.session['tmp_dir']


def remove_from_computation_recs(request, exp):

    logger.debug('Removing experiment %s from computation_recs in session', exp)
    computation_recs = request.session.get('computation_recs', [])
    exp_id = exp.pk
    computation_recs[:] = [r for r in computation_recs if r['experiment']['exp_id'] != exp_id]
    request.session['computation_recs'] = computation_recs


def cart_add(request, pk):
    """ add an experiment to the analysis cart and return"""

    pk=int(pk) # make integer for lookup within template
    analyze_list = request.session.get('analyze_list', [])
    if pk not in analyze_list:
        analyze_list.append(pk)
    request.session['analyze_list'] = analyze_list

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def cart_del(request, pk):
    """ remove an experiment from the analysis cart and return"""

    pk=int(pk) # make integer for lookup within template
    analyze_list = request.session.get('analyze_list', [])
    if pk in analyze_list:
        analyze_list.remove(pk)
    request.session['analyze_list'] = analyze_list

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def cart_empty(request):
    """ remove all experiments from the analysis cart and return"""

    request.session['analyze_list'] = []
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def cart_add_all(request):
    """ add all experiments to the analysis cart and return"""

    exps = Experiment.objects.all()
    request.session['analyze_list'] = [e.pk for e in exps]
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def cart_edit(request, pk=None):
    """ create a list of experiments to analyze / display the list"""

    if request.method == 'POST':
        form = ExperimentConfirmForm(request.POST)
        if form.is_valid():

            retained_ids = []
            for exp in form.cleaned_data['experiments']:
                retained_ids.append(exp.pk)

            logger.debug('Experiments for analysis being saved in session: %s', retained_ids)
            request.session['analyze_list'] = retained_ids

            if request.POST.get('_addanother') is not None:
                return HttpResponseRedirect(request.POST.get('referrer'))
            else:
                return HttpResponseRedirect(reverse('tp:analysis-summary'))

    else:

        form = ExperimentConfirmForm()
        # check that this exp_id is valid exp
        if pk:
            get_object_or_404(Experiment, pk=pk)

        analyze_list = request.session.get('analyze_list', [])
        if pk and pk not in analyze_list:
            analyze_list.append(pk)

        if not analyze_list:
            message = 'Please add experiments to analyze from the experiments list first'
            redirect_url = reverse('tp:experiments')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            return render(request, 'generic_message.html', context)
        elif len(analyze_list) > 50:
            message = 'Too many experiments in the cart to display; if analyzing all experiments do not try to edit the list. Either select analyze or empty cart'
            redirect_url = reverse('tp:experiments')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            return render(request, 'generic_message.html', context)
        else:
            request.session['analyze_list'] = analyze_list
            # override the default queryset which is all samples
            form.fields['experiments'].queryset = Experiment.objects.filter(pk__in=analyze_list)

    context = {'form': form}
    return render(request, 'cart_edit.html', context)


def analysis_summary(request):
    """  prepare page that presents the analysis summary """

    analyze_list = request.session.get('analyze_list', [])

    if not analyze_list:
        message = 'Potential bug; accessing analysis_landing with no exps in analysis cart'
        context = {'message': message, 'error': True}
        return render(request, 'generic_message.html', context)

    exps = Experiment.objects.filter(pk__in=analyze_list)
    context = {'experiments': exps}
    return render(request, 'analysis_summary.html', context)


def experiments_confirm(request):
    """ allow editing of experiments for which data will be uploaded """

    if request.method == 'POST':
        form = ExperimentConfirmForm(request.POST)
        if form.is_valid():

            retained_ids = []
            for exp in form.cleaned_data['experiments']:
                retained_ids.append(exp.pk)

            study = get_study_from_session(request.session)
            exps = Experiment.objects.filter(study=study).all()
            del_exps = list()
            for e in exps:
                if e.id not in retained_ids:
                    del_exps.append(e.experiment_name)
                    e.delete()

            if del_exps:
                logger.info('Deleted the following non-selected experiments: %s', del_exps)

            # if deleted all existing samples by not checking any exps, need to add more before sample upload
            if request.POST.get('_continue') is not None and len(retained_ids) > 0:
                return HttpResponseRedirect(reverse('tp:samples-confirm'))
            elif request.POST.get('_add') is not None:
                return HttpResponseRedirect(reverse('tp:experiment-add'))
            else:
                message = 'Found bug in experiments_confirm; please report'
                context = {'message': message, 'error': True}
                return render(request, 'generic_message.html', context)

    else:
        # set the value of study based on session content
        study = get_study_from_session(request.session)
        if study is None:
            message = 'Potential bug in experiments_confirm; Please add or edit a study first and retry'
            redirect_url = reverse('tp:studies')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            return render(request, 'generic_message.html', context)

        exps = Experiment.objects.filter(study=study).all()

        # if there aren't any existing experiments, skip this dialog and go straight to addition
        if len(exps) == 0:
            return HttpResponseRedirect(reverse('tp:experiment-add'))

        form = ExperimentConfirmForm()
        # override the default queryset which is all exps
        form.fields['experiments'].queryset = exps

    context = {'form': form}
    logger.debug('Have %s', form.fields['experiments'].choices)
    return render(request, 'experiments_confirm.html', context)


def samples_confirm(request):
    """ review existing samples in database during study data upload """

    if request.method == 'POST':
        form = SampleConfirmForm(request.POST)
        if form.is_valid():

            retained_ids = []
            for s in form.cleaned_data['samples']:
                retained_ids.append(s.pk)

            study = get_study_from_session(request.session)
            smpls = Sample.objects.filter(study=study).all()
            del_smpls = list()
            for s in smpls:
                if s.id not in retained_ids:
                    del_smpls.append(s.sample_name)
                    # delete any existing associations to experiment for this sample
                    ExperimentSample.objects.filter(sample=s).delete()
                    s.delete()

            if del_smpls:
                logger.info('Deleted the following non-selected samples: %s', del_smpls)

            # if deleted all existing samples by not checking any smpls, need to add more before sample upload
            if request.POST.get('_continue') is not None and len(retained_ids) > 0:
                return HttpResponseRedirect(reverse('tp:experiment-sample-add'))
            elif request.POST.get('_add') is not None:
                return HttpResponseRedirect(reverse('tp:samples-upload'))
            else:
                message = 'Found bug in samples_confirm; please report'
                context = {'message': message, 'error': True}
                return render(request, 'generic_message.html', context)

    else:
        # set the value of study based on session content
        study = get_study_from_session(request.session)
        if study is None:
            message = 'Potential bug in sample_confirm; Please add or edit a study first and retry'
            redirect_url = reverse('tp:studies')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            return render(request, 'generic_message.html', context)

        smpls = Sample.objects.filter(study=study).all()

        # if revising an existing, it's possible to move to experiment-vs-sample dialog without ever uploading
        # a file (and hence setting sample_files and other stuff in session; force use of sample upload handler
        # Also, if there aren't any existing samples, skip this dialog and go straight to upload handler
        if len(smpls) == 0 or request.session.get('sample_file', None) is None:
            return HttpResponseRedirect(reverse('tp:samples-upload'))

        form = SampleConfirmForm()
        # override the default queryset which is all smpls
        form.fields['samples'].queryset = smpls

    context = {'form': form}
    return render(request, 'samples_confirm.html', context)


def create_samples(request):
    """ allow bulk creation/edit of samples from uploaded file """

    #TODO - Nasty bug where if you make mistake and select upload single sample and select file
    # and then realize and go back and select the correct multiple files -- only the initial file
    # will be uploaded to the tmpdir. However, the other samples are in the session and it appears
    # to work until you launch the computation
    skipped_from_file = list()

    if request.method == 'POST':
        formset = SampleFormSet(request.POST)
        if formset.is_valid():
            # TODO - there's a bug whereby if one of the samples is deleted on the form
            # the last one itself is not kept.  Not a simple matter of hitting null in list
            # since you can delete the first one and 2, 3, ... come through just not the last one
            # can also get this if you delete all orig ones and hand-enter new sample names
            study = get_study_from_session(request.session)
            samples = formset.save(commit=False)
            # need to save the study which was not in the formset
            for s in samples:
                s.study = study
                s.save()
            return HttpResponseRedirect(reverse('tp:samples-confirm'))

    else:
        initial = []
        extra = 0

        study = get_study_from_session(request.session)
        if study is None:
            message = 'Potential bug in create_samples; Please upload your results data files first'
            redirect_url = reverse('tp:samples-upload')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            return render(request, 'generic_message.html', context)

        # get list of existing samples previously uploaded
        samples = Sample.objects.filter(study=study).all()
        have_samples = list()
        if samples:
            # delete any existing exp-vs-sample associations - force re-association whenever reloading from files
            ExperimentSample.objects.filter(sample__in=samples).delete()

            have_samples = [s.sample_name for s in samples]

        # set the value of study based on session content
        if request.session.get('added_sample_names', None) is None:
            message = 'Potential bug in create_samples; Please upload your results data files first'
            redirect_url = reverse('tp:samples-upload')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            logger.error('Did not retrieve samples from uploaded file; form will be blank')
            return render(request, 'generic_message.html', context)
        else:
            for sample_name in request.session['added_sample_names']:
                if have_samples and sample_name in have_samples:
                    skipped_from_file.append(sample_name)
                    continue

                initial.append({'sample_name': sample_name})
                extra += 1

        # all the uploaded samples already exist in database; move on to confirm
        if not initial:
            logger.debug('All uploaded samples already in database; skip to confirm samples')
            return HttpResponseRedirect(reverse('tp:samples-confirm'))

        # get an empty form (in terms of existing samples) but pre-populate from loaded sample names
        formset = SampleFormSet(queryset=Sample.objects.none(), initial=initial)
        setattr(formset, 'extra', extra)

    return render(request, 'samples_add_form.html', {'formset': formset, 'existing_samples': skipped_from_file})


def create_experiment_sample_pair(request, reset=None):
    """ create_experiment_sample_pair -- create association between experiments and samples """

    if request.method == 'POST':
        form = ExperimentSampleForm(request.POST)
        if form.is_valid():

            exp_id = form.cleaned_data['exp_id']
            exp = Experiment.objects.get(pk=exp_id)
            # create a record that will be passed to group fold change computation script
            process_rec = {'experiment': {'exp_id': exp_id, 'exp_name': exp.experiment_name},
                           'sample': [], 'experiment_vs_sample': []}

            # JS: why not simply use django models with many-to-many relationship and let a CBV handle it?
            # some samples can be control for certain comparisons, and intervention for others; i.e. a sham
            # animal is a control for real surgery but can be intervention compared to a naive animal. Probably best
            # to take full control of process ...
            for s in form.cleaned_data['trt_samples']:
                rec = ExperimentSample(sample=s, experiment=exp, group_type = 'I')
                rec.save()
                process_rec['sample'].append({'sample_id': s.pk, 'sample_name': s.sample_name, 'sample_type': 'I'})
                process_rec['experiment_vs_sample'].append(rec.pk)

            for s in form.cleaned_data['ctl_samples']:
                rec = ExperimentSample(sample=s, experiment=exp, group_type = 'C')
                rec.save()
                process_rec['sample'].append({'sample_id': s.pk, 'sample_name': s.sample_name, 'sample_type': 'C'})
                process_rec['experiment_vs_sample'].append(rec.pk)

            # add the current experiment definition to session
            computation_recs = request.session.get('computation_recs', [])
            computation_recs.append(process_rec)
            request.session['computation_recs'] = computation_recs
            # keep sending back to the same form until all newly-added experiments have sample associations
            return HttpResponseRedirect(reverse('tp:experiment-sample-add'))
    else:

        # retrieve newly added experiments
        study = get_study_from_session(request.session)
        exps = list()
        samples = list()

        if study is not None:
            exps = Experiment.objects.filter(study=study).all()
            samples = Sample.objects.filter(study=study).all()

        if not exps or not samples:
            message = 'Potential bug; Please add new experiments for which you want to upload data first'
            redirect_url = reverse('tp:experiment-add')
            errcontext = {'message': message, 'redirect_url': redirect_url, 'error': True}
            logger.error('Did not retrieve experiments from session')
            return render(request, 'generic_message.html', errcontext)

        # clearing some/all exp-sample associations
        if reset and reset.lower() == 'all':
            logger.debug('clearing all existing sample associations for study %s', study.study_name)
            ExperimentSample.objects.filter(experiment__in=exps).delete()
            # if deleted exps. vs sample assoc was set in session on post side of view, delete
            for e in exps:
                remove_from_computation_recs(request, e)
        elif reset:
            try:
                this_exp = Experiment.objects.get(pk=reset)
            except:
                message = 'Potential bug; ID {} supplied to create_experiment_sample_pair is not valid experiment'.format(reset)
                errcontext = {'message': message, 'error': True}
                logger.error('Received %s to reset experiment-sample associations and not valid experiment ID', reset)
                return render(request, 'generic_message.html', errcontext)
            logger.debug('clearing existing sample associations for experiment %s', reset)
            ExperimentSample.objects.filter(experiment=this_exp).delete()
            remove_from_computation_recs(request, this_exp)
        # create a list of which exps that go with this study
        # we iterate through all experiments and keep hitting this view until all experiments have had samples
        # associated with them
        selected_exp = None
        for e in exps:
            # only check on exp ... samples can be used multiple times (e.g. controls)
            has_sample_assoc = ExperimentSample.objects.filter(experiment=e).first()
            if has_sample_assoc is None:
                selected_exp = e
                break

        # done with association of these exps to samples
        if selected_exp is None:
            return HttpResponseRedirect(reverse('tp:experiment-sample-confirm'))

        # pre-select the experiment in question in the form as that we're working on
        form = ExperimentSampleForm(initial={'exp_id': selected_exp.pk})
        # override the default queryset which is all samples
        form.fields['trt_samples'].queryset = samples
        form.fields['ctl_samples'].queryset = samples

    context = {'form': form, 'selected_experiment': selected_exp}
    return render(request, 'experiment_vs_sample_form.html', context)


def confirm_experiment_sample_pair(request):
    """ display table of experiment vs. samples that will be processed """

    if request.method == 'POST':
        tmpdir = request.session.get('tmp_dir')
        computation_config = settings.COMPUTATION
        json_cfg = dict(experiments=request.session.get('computation_recs'),
                        file_name=request.session.get('sample_file'),
                        file_type=request.session.get('sample_type'),
                        tmpdir=request.session.get('tmp_dir'),
                        script_dir=computation_config["script_dir"])
        file = os.path.join(tmpdir, 'computation_data.json')
        logger.debug('json job config file:  %s', file)
        with open(file, 'w') as outfile:
            json.dump(json_cfg, outfile)
        request.session['computation_config'] = file
        return HttpResponseRedirect(reverse('tp:compute-fold-change'))

    else:
        if request.session.get('computation_recs', None) is None:
            message = 'confirm_experiment_sample_pair: no computation_recs session variable; report bug'
            context = {'message': message, 'error': True}
            logger.error('no computation_recs session variable')
            return render(request, 'generic_message.html', context)

        if request.session.get('tmp_dir', None) is None:
            message = 'confirm_experiment_sample_pair: no tmp_dir session variable; report bug'
            context = {'message': message, 'error': True}
            logger.error('no tmp_dir session variable')
            return render(request, 'generic_message.html', context)

        data = request.session['computation_recs']
        table_ids = []
        for row in data:
            table_ids += row['experiment_vs_sample']

        logger.debug('computation_recs stored in session: %s', pprint.pformat(data))
#        table_content = ExperimentSample.objects.filter(pk__in=table_ids)
#        for row in table_content:
#            logger.debug('Content of row %s, %s, %s', row.group_type, row.sample, row.experiment)
#
#        context = {'table': table_content}
        return render(request, 'experiment_vs_sample_confirm.html', {'data': data})


def compute_fold_change(request):
    """ run computation script on meta data stored in session """

    user = None
    if request.user.is_authenticated():
        user = request.user

    if request.method == 'POST':
        # once job is complete, clear all the session variables used in process
        reset_session(request.session)
        return HttpResponseRedirect(reverse('tp:experiments'))

    else:
        # TODO - Should move most of this to the Computation.calc_fold_change location to keep this cleaner
        tmpdir = request.session.get('tmp_dir')
        cfg_file = request.session.get("computation_config")
        logger.debug('compute_fold_change: json job config file:  %s', cfg_file)
        with open(cfg_file) as infile:
            json_cfg = json.load(infile)
            experiments = json_cfg['experiments']
        # need to make sure world readable as script run by different user
        for f in os.listdir(tmpdir):
            logger.debug("chmod on %s", f)
            os.chmod(os.path.join(tmpdir, f), 0o777)
        # create context to send back to web page
        context = dict()
        n_samples = 0
        for e in experiments:
            n_samples += len(e['sample'])
        context['n_samples'] = n_samples
        res = process_user_files.delay(tmpdir, cfg_file, user.email)
        logger.debug("compute_fold_change: config %s", pprint.pformat(experiments))

        context['email'] = user.email
        context['result'] = res
        logger.debug("compute_fold_change: web context: %s", pprint.pformat(context))

        return render(request, 'compute_fold_change.html', context)


def export_result_xls(request, restype=None):
    """ query module / GSA / gene fold change and return excel file """
    
    rowlimit = 100000
    limit_breached = False
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="analysis_results.xls"'

    # if session contains experiment IDs from cart selection, filter to them
    exp_list = request.session.get('analyze_list', [])
    if not exp_list:
        message = 'Please report bug: trying to export results with no selected experiments in cart'
        context = {'message': message, 'error': True}
        return render(request, 'generic_message.html', context)

    colnames = ['experiment id', 'experiment name']
    data = list()
    subset = list()

    # restype will be None when coming from interactive filtered views of results; get it out of the session
    if restype is None:
        if request.session.get('filtered_type', None) is None:
            message = 'Potential bug: trying to export results from filtered view with no info on result type in session; did you try exporting an empty result set?'
            context = {'message': message, 'error': True}
            logger.error('Trying to export results from filtered view with no info on result type in session')
            return render(request, 'generic_message.html', context)

        # retrieve the subset of records to be included in the excel file
        subset = request.session.get('filtered_list', [])
        restype = request.session['filtered_type']
        logging.info('Retrieving results from filtered view for result type %s and %s pre-filtered results', restype, len(subset))

    if restype.lower() == 'modulescores':
        colnames += ['module', 'type', 'description', 'score']
        rows = ModuleScores.objects.filter(experiment__pk__in=exp_list)
        if subset:
            rows = rows.filter(pk__in=subset)

        rowcount = 0
        for r in rows:
            nr = [r.experiment_id, r.experiment.experiment_name, r.module.name, r.module.type, r.module.desc, r.score]
            data.append(nr)
            rowcount += 1
            if rowcount > rowlimit:
                limit_breached = True
                break

    elif restype.lower() == 'gsascores':
        colnames += ['gene set', 'type', 'description', 'source', 'score', 'p-adj']
        rows = GSAScores.objects.filter(experiment__pk__in=exp_list)
        if subset:
            rows = rows.filter(pk__in=subset)

        rowcount = 0
        for r in rows:
            nr = [r.experiment_id, r.experiment.experiment_name, r.geneset.name, r.geneset.type, r.geneset.desc, r.geneset.source, r.score, r.p_bh]
            data.append(nr)
            rowcount += 1
            if rowcount > rowlimit:
                limit_breached = True
                break

    elif restype.lower() == 'foldchangeresult':
        colnames += ['gene_identifier', 'rat entrez gene ID', 'rat gene symbol', 'log2 fold change', 'treatment samples', 'control samples', 'expression avg controls', 'p', 'p-adj']
        rows = FoldChangeResult.objects.filter(experiment__pk__in=exp_list)
        if subset:
            rows = rows.filter(pk__in=subset)

        rowcount = 0
        for r in rows:
            nr = [r.experiment_id, r.experiment.experiment_name, r.gene_identifier.gene_identifier, r.gene_identifier.gene.rat_entrez_gene, r.gene_identifier.gene.rat_gene_symbol, r.log2_fc, r.n_trt, r.n_ctl, r.expression_ctl, r.p, r.p_bh]
            data.append(nr)
            rowcount += 1
            if rowcount > rowlimit:
                limit_breached = True
                break

    elif restype.lower() == 'experimentcorrelation':
        colnames += ['experiment_ref_id', 'experiment_ref_name', 'method', 'Pearson R', 'rank']
        rows = ExperimentCorrelation.objects.filter(experiment__pk__in=exp_list)
        if subset:
            rows = rows.filter(pk__in=subset)

        rowcount = 0
        for r in rows:
            nr = [r.experiment_id, r.experiment.experiment_name, r.experiment_ref_id, r.experiment_ref.experiment_name, r.source, r.correl, r.rank]
            data.append(nr)
            rowcount += 1
            if rowcount > rowlimit:
                limit_breached = True
                break

    elif restype.lower() == 'toxicologyresult':

        colnames += ['result type', 'result name', 'group average', 'animal details']
        # diff patern here compared to other result types; for toxicologyresult the filtered result IDs may not involve
        # the experiments in the cart when results are for the ref_exp_ids in SimilarExperiments view
        if subset:
            rows = ToxicologyResult.objects.filter(pk__in=subset)
        else:
            rows = ToxicologyResult.objects.filter(experiment__pk__in=exp_list)

        rowcount = 0
        for r in rows:
            nr = [r.experiment_id, r.experiment.experiment_name, r.result_type, r.result_name, r.group_avg, r.animal_details]
            data.append(nr)
            rowcount += 1
            if rowcount > rowlimit:
                limit_breached = True
                break

    else:
        raise NotImplementedError ('Type not implemented:', restype)

    # warn user that output was limited ... avoid too-large excel spreadsheet
    if limit_breached:
        logger.info('Excel output was truncated')
        nr = ['output truncated'] * len(colnames)
        data.append(nr)

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet(restype)

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in range(len(colnames)):
        ws.write(row_num, col_num, colnames[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    for row in data:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


class ResetSessionMixin(object):

    # TODO - better way to call an arbitary function (reset_session) on CBV lisview?
    def get_context_data(self, **kwargs):

        # only reason for doing this is to force a reset of session when flow from study->sample upload is interrupted
        reset_session(self.request.session)
        context = super(ResetSessionMixin, self).get_context_data(**kwargs)
        return context


class StudyView(ResetSessionMixin, SingleTableView):
    model = Study
    template_name = 'study_list.html'
    context_object_name = 'studies'
    table_class = tp.tables.StudyListTable
    table_pagination = True

    def get_queryset(self):
        # to ensure that only a user's study are shown to him/her
        new_context = Study.objects.filter(owner_id=self.request.user.id)
        return new_context


class StudyCreateUpdateMixin(object):

    def get_success_url(self):

        if self.request.POST.get('_save_ret') is not None:
            return reverse('tp:studies')
        elif self.request.POST.get('_save_add_exp') is not None:
            return reverse('tp:experiments-confirm')
        elif self.request.POST.get('_continue') is not None:
            return reverse('tp:study-update', kwargs={'pk': self.object.pk})
        else:
            # the default behavior for Study object
            return reverse('tp:studies')

    def form_valid(self, form):

        url = super(StudyCreateUpdateMixin, self).form_valid(form)

        # set up the session so that experiment and sample additions can display study info
        reset_session(self.request.session)
        self.request.session['adding_study'] = {'id': self.object.pk, 'name': self.object.study_name}
        logger.debug('cleared session and re-init to %s', self.request.session['adding_study'])

        return url


class StudyCreate(StudyCreateUpdateMixin, CreateView):
    """ StudyCreate -- view class to handle creation of a user study """
    model = Study
    template_name = 'study_form.html'
    form_class = StudyForm
    success_url = reverse_lazy('tp:studies')


class StudyUpdate(StudyCreateUpdateMixin, UpdateView):
    """ StudyUpdate -- view class to handle updating values of a user study """
    model = Study
    template_name = 'study_form.html'
    form_class = StudyForm
    success_url = reverse_lazy('tp:studies')


class StudyDelete(DeleteView):
    """ StudyDelete -- view class to handle deletion of study """
    model = Study
    template_name = 'study_confirm_delete.html'
    success_url = reverse_lazy('tp:studies')


class ExperimentView(ResetSessionMixin, SingleTableView):
    model = Experiment
    template_name = 'experiments_list.html'
    context_object_name = 'experiments'
    table_class = tp.tables.ExperimentListTable
    table_pagination = True

    def get_context_data(self, **kwargs):

        context = super(ExperimentView, self).get_context_data(**kwargs)
        analyze_list = self.request.session.get('analyze_list', [])
        cart_items = len(analyze_list)
        context['cart_items'] = cart_items
        return context

    def get_queryset(self):

        user_query = self.request.GET.get('query')
        only_mine = self.request.GET.get('onlymyexp')
        if user_query:

            logger.debug('User query is %s', user_query)
            terms = user_query.split()

            # TODO - should be able to use the SearchRank method, but gives awful results when combining multiple terms
            # like 'diazepam single'
            # note that query must be something like SearchQuery('diazepam') & SearchQuery('single')
            # exps = Experiment.objects.annotate(rank=SearchRank(vector, query)).order_by('-rank')
            # instead running multiple searches, one per keyword and combining

            vector = SearchVector('experiment_name',
                                  'compound_name',
                                  'tissue',
                                  'organism',
                                  'strain')

            first = terms.pop(0)
            exps = Experiment.objects.annotate(search=vector).filter(search__contains=first)
            logger.debug('First user term %s returned %s hits', first, len(exps))

            while terms:
                this = terms.pop(0)
                logger.debug('Searching on term %s', this)
                exps = exps.annotate(search=vector).filter(search__contains=this)
                logger.debug('Subsequent user term %s reduced to %s hits', this, len(exps))

            logger.debug('User query returned %s', exps)
        else:
            exps = Experiment.objects.all()
            logger.debug('Standard query returned %s', exps)

        if only_mine and self.request.user.is_authenticated():
            exps = exps.filter(study__owner=self.request.user)
            logger.debug('Query after filtering on user returned %s', exps)

        return exps


class ExperimentSuccessURLMixin(object):

    def get_success_url(self):

        # upon success, make sure that any previous use of _addanother is forgotten
        self.request.session['last_exp_id'] = None

        if self.request.POST.get('_addanother') is not None:
            # store the id of this object in order to pre-fill next one
            self.request.session['last_exp_id'] = self.object.pk
            return reverse('tp:experiment-add')
        elif self.request.POST.get('_continue') is not None:
            return reverse('tp:experiment-update', kwargs={'pk': self.object.pk})
        elif self.request.POST.get('_save') is not None:
            return reverse('tp:experiments-confirm')
        elif self.request.POST.get('_save_ret') is not None:
            return reverse('tp:experiments')
        else:
            # the default behavior for Experiment object
            return reverse('tp:samples-add')


class ExperimentDetailView(DetailView):
    model = Experiment
    template_name = 'experiment_detail.html'


class ExperimentCreate(ExperimentSuccessURLMixin, CreateView):
    """ ExperimentCreate -- view class to handle creation of a user experiment """

    model = Experiment
    template_name = 'experiment_form.html'
    form_class = ExperimentForm

    def get_initial(self):
        # Get the initial dictionary from the superclass method
        initial = super(ExperimentCreate, self).get_initial()

        # prepopulate experiment based on last one
        if self.request.session.get('last_exp_id', None) is not None:
            last_exp_id = self.request.session['last_exp_id']
            logger.debug('Retrieved prior experiment ID %s', last_exp_id)
            last_exp = Experiment.objects.get(pk=last_exp_id)
            # TODO - remove experiment name assuming that this will be prepopulated by other meta data
            fields = ['experiment_name', 'tech', 'compound_name', 'dose', 'dose_unit', 'time', 'tissue',
                      'organism', 'strain', 'gender', 'single_repeat_type', 'route']
            for f in fields:
                initial[f] = getattr(last_exp, f)

            logger.info('prepopulated object %s', pprint.pformat(initial))

        return initial

    def get_context_data(self, **kwargs):

        context = super(ExperimentCreate, self).get_context_data(**kwargs)

        # set the value of study based on session content
        studyobj = get_study_from_session(self.request.session)
        if studyobj is None:
            context['study_error'] = 'Potential bug; Please try adding a new study before adding new experiments'
            logger.error('creating experiment without study info in session')
            return context

        return context

    def form_valid(self, form):

        try:
            study = Study.objects.get(pk=self.request.session['adding_study']['id'])
        except:
            logger.error('study ID stored in session is not valid')
            return self.form_invalid(form)

        # the study field is not exposed and the form and is a required value - prepopulate
        form.instance.study = study
        url = super(ExperimentCreate, self).form_valid(form)
        return url


class ExperimentUpdate(ExperimentSuccessURLMixin, UpdateView):
    """ ExperimentUpdate -- view class to handle updating values of a user experiment """
    model = Experiment
    template_name = 'experiment_form.html'
    form_class = ExperimentForm


class ExperimentDelete(DeleteView):
    """ ExperimentDelete -- view class to handle deletion of experiment """
    model = Experiment
    template_name = 'experiment_confirm_delete.html'
    success_url = reverse_lazy('tp:experiments')


class SampleSuccessURLMixin(object):

    def get_success_url(self):

        if self.request.POST.get('_save') is not None:
            return reverse('tp:sample-add')
        elif self.request.POST.get('_continue') is not None:
            return reverse('tp:sample-update', kwargs={'pk': self.object.pk})
        elif self.request.POST.get('_save_ret') is not None:
            return reverse('tp:samples')
        else:
            # the default behavior for Sample object
            return reverse('tp:samples')


class SampleView(ResetSessionMixin, ListView):
    model = Sample
    template_name = 'samples_list.html'
    context_object_name = 'samples'
    paginate_by = 25


class SampleCreate(SampleSuccessURLMixin, CreateView):
    """ SampleCreate -- view class to handle creation of a user experiment """
    model = Sample
    template_name = 'sample_form.html'
    form_class = SampleForm
    success_url = reverse_lazy('tp:sample-add')

    def get_context_data(self, **kwargs):

        context = super(SampleCreate, self).get_context_data(**kwargs)

        # set the value of study based on session content
        if self.request.session.get('adding_study', None) is None:
            context['study_error'] = 'Potential bug; Please try adding a new study before adding new samples'
            logger.error('creating sample without study info in session')
            return context

        try:
            Study.objects.get(pk=self.request.session['adding_study']['id'])
        except:
            context['study_error'] = 'Study ID stored in session is not valid; report bug'
            logger.error('study ID stored in session is not valid')

        return context

    def form_valid(self, form):

        try:
            study = Study.objects.get(pk=self.request.session['adding_study']['id'])
        except:
            logger.error('study ID stored in session is not valid')
            return self.form_invalid(form)

        form.instance.study = study
        url = super(SampleCreate, self).form_valid(form)
        return url


class SampleUpdate(SampleSuccessURLMixin, UpdateView):
    """ SampleUpdate -- view class to handle updating values of a user sample """
    model = Sample
    template_name = 'sample_form.html'
    form_class = SampleForm
    success_url = reverse_lazy('tp:samples')


class SampleDelete(DeleteView):
    """ SampleDelete -- view class to handle deletion of sample """
    model = Sample
    template_name = 'sample_confirm_delete.html'
    success_url = reverse_lazy('tp:samples')


class UploadSamplesView(FormView):
    template_name = 'samples_upload.html'
    form_class = FilesForm
    success_url = reverse_lazy('tp:samples-add')

    def get_context_data(self, **kwargs):

        context = super(UploadSamplesView, self).get_context_data(**kwargs)

        study = get_study_from_session(self.request.session)
        exps = list()
        if study:
            exps = Experiment.objects.filter(study=study).all()

        if study is None or not exps:
            message = 'Potential bug; Please add experiments to analyze from the experiments list first'
            redirect_url = reverse('tp:experiments')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            logger.error('Did not retrieve study from session or existing experiments')
            return render(self.request, 'generic_message.html', context)
        else:
            added_names = [o.experiment_name for o in exps]
            context['added_exp_names'] = added_names

        return context

    def post(self, request, *args, **kwargs):

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        # TODO write custom upload handlers to send files directly working directory instead of loading them
        # https://docs.djangoproject.com/en/1.10/ref/files/uploads/#custom-upload-handlers
        if form.is_valid():

            samples_added = []
            if request.FILES.get('single_file', None) is not None:
                tmpdir = get_temp_dir(self)
                f = request.FILES.get('single_file')
                fs = FileSystemStorage(location=tmpdir)
                fs.save(f.name, f)
                self.request.session['sample_file'] = f.name
                self.request.session['sample_type'] = "RNAseq"
                logger.debug("reading samples names from single file %s in dir %s", f.name, tmpdir)
                rnafile = os.path.join(tmpdir, f.name)
                if os.path.isfile(rnafile):
                    with open(rnafile, newline='') as txtfile:
                        txtreader = csv.reader(txtfile, delimiter='\t')
                        header = next(txtreader)
                        header.pop(0) # remove first column
                        logger.debug(pprint.pformat(header))
                        for s in header:
                            samples_added.append(s)
                else:
                    logger.warning("unable to read uploaded file % in dir %s", f.name, tmpdir)
                        # TODO - read and parse the first row to get the sample names, append to samples_added
                #samples_added = some_future_call()
            elif request.FILES.getlist('multiple_files'):
                tmpdir = get_temp_dir(self)
                self.request.session['sample_file'] = 'cel:in_directory'
                self.request.session['sample_type'] = "CEL"
                mult_files = request.FILES.getlist('multiple_files')
                for f in mult_files:
                    sample_name = os.path.splitext(f.name)[0]
                    samples_added.append(sample_name)
                    fs = FileSystemStorage(location=tmpdir)
                    fs.save(f.name, f)
            else:
                return self.form_invalid(form)

            # store the newly added samples in session for next handler
            logger.debug('adding %s samples to experiment', len(samples_added))
            self.request.session['added_sample_names'] = samples_added

            return self.form_valid(form)

        else:
            return self.form_invalid(form)


class UploadTechMapView(FormView):

    template_name = 'techmap_upload.html'
    form_class = MapFileForm
    success_url = reverse_lazy('tp:experiment-add')

    def post(self, request, *args, **kwargs):

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        #TODO - same thing as above, don't load into memory then dump out again
        if form.is_valid() and request.FILES.get('map_file', None) is not None:
            f = request.FILES.get('map_file')
            tmpdir = get_temp_dir(self)
            fs = FileSystemStorage(location=tmpdir)
            local_file = fs.save(f.name, f)
            full_path_file = os.path.join(tmpdir, local_file)

            #TODO - either use it with the .delay option in celery or add a spinning bar to show upload in progress - takes ~1 minute for 15k recs
            status = load_measurement_tech_gene_map(full_path_file)
            if status:
                #TODO - could create a new success URL that loads a message showing name of array platforms and number of recs loaded
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)


class FilteredSingleTableView(SingleTableView):
    filter_class = None

    def get_table_data(self):

        data = super(FilteredSingleTableView, self).get_table_data()

        # when tox results are being viewed for the most similar experiments (given those in analyze_list), we want to
        # query based on the stored attribute set when those results were being viewed
        referrer = self.request.META.get('HTTP_REFERER', None)
        sim_list = self.request.session.get('sim_list', [])
        exp_list = self.request.session.get('analyze_list', [])
        used_simexp = False

        # when accessing ToxicologyResults from the analysis_summary, reset the list of similar experiments so that
        # additional queries on the class (when user filters results) is not recognized as having come from Sim Exps
        # (the referrer will be itself)
        # TODO - a better way to check referrer? what if URL is setup differently?
        if type(self).__name__ == 'ToxicologyResultsSingleTableView' and referrer and 'analysis_summary' in referrer:
            logger.debug('Resetting stored list of similar experiments since referrer was analysis_summary')
            sim_list = list()
            self.request.session['sim_list'] = sim_list

        # cannot check the referrer as coming from SimilarExperiments, because subsequent views by user using filtering
        # will show the referrer at itself; that's why sim_list is cleared above for access through analysis_summary
        if type(self).__name__ == 'ToxicologyResultsSingleTableView' and sim_list:
            logger.debug('Accessing ToxicologyResults after viewing SimilarExperiments; using ref pairs to query exps')
            expcorrel_objs = ExperimentCorrelation.objects.filter(id__in=sim_list)
            ref_exp_list = map(lambda x: x.experiment_ref.id, expcorrel_objs)
            data = data.filter(experiment__pk__in=ref_exp_list)
            used_simexp = True

        # standard use where someone has a handful of experiments in cart - query the complete dataset
        elif exp_list and len(exp_list) < 100:
            logger.debug('Filtering to subset of experiments in cart: %s', exp_list)
            data = data.filter(experiment__pk__in=exp_list)
        # very long list of experiments, most likely all experiments in the cart; filtering on exp list is performance
        # killer
        # TODO currently the experiment list is completely ignored, most likely fine as someone with 100 exps in the
        # cart is looking at global trends
        elif exp_list:
            logger.debug('More than 100 items in cart; not filtering by experiment')
            pass

        self.filter = self.filter_class(self.request.GET, queryset=data)
        results = self.filter.qs

        # if the current result list is from SimilarExperiments, store the result IDs so that ref experiments can be
        # accessed in subsequent ToxicologyResults view
        if type(self).__name__ == 'SimilarExperimentsSingleTableView':
            ids = list(results.values_list('id', flat=True))
            logger.debug('Storing retrieved data in session for subsequent ToxicologyResult view')
            self.request.session['sim_list'] = ids

        # store the object IDs in case data is exported to excel via separate handler
        # reset filtering session vars from any previous use
        self.request.session['filtered_list'] = []
        self.request.session['filtered_type'] = None

        # TODO - will generate an error if someone tries exporting a set with nothing in it
        # if exporting from excel, need to know what kind of data (module, pathway, etc) was being examined.
        # Is there a better way to store in general way type of sub-classed view using this?
        # TODO - need to store a trigger than some set of results was filtered; will replace the Or False
        # Why two part conditional statement? small list of experiments (typical user case, i.e. viewing results for my
        # experiments), store either the full set of results or filtered set.  Full set meaning someone is viewing all
        # module results, and they don't do any filtering.  They want to export all the results.  Other case is when
        # viewing all experiments in cart.  Here, unless they actually filter to something first, don't allow export.
        # Once they filtered to a gene or something reasonable, then run this block.  Otherwise, performance is very slow
        if len(exp_list) < 100 and len(self.filter.qs) > 0 or False:
            self.request.session['filtered_type'] = results[0].__class__.__name__

            # no need to store long list of ids for viewed results if nothing was filtered (although maybe this is
            # harmless, didn't do any performance testing).
            # However, force storage of selected IDs when working with ToxicologyResults through SimilarExperiments, so
            # that subsequent excel export does not revert to using the experiments in analysis cart
            if len(self.filter.qs) < len(data) or used_simexp:
                ids = list(results.values_list('id', flat=True))
                logger.debug('Retrieved data of length %s being stored in session:  %s', len(results), ids)
                self.request.session['filtered_list'] = ids

        return results

    def get_context_data(self, **kwargs):

        context = super(FilteredSingleTableView, self).get_context_data(**kwargs)
        context['filter'] = self.filter
        if type(self).__name__ == 'SimilarExperimentsSingleTableView':
            context['show_tox_result_link'] = True
        return context


class ModuleFilteredSingleTableView(FilteredSingleTableView):
    model = ModuleScores
    template_name = 'result_list.html'
    table_class = tp.tables.ModuleScoreTable
    table_pagination = True
    filter_class = tp.filters.ModuleScoreFilter


class GSAFilteredSingleTableView(FilteredSingleTableView):
    model = GSAScores
    template_name = 'result_list.html'
    table_class = tp.tables.GSAScoreTable
    table_pagination = True
    filter_class = tp.filters.GSAScoreFilter


class FoldChangeSingleTableView(FilteredSingleTableView):
    model = FoldChangeResult
    template_name = 'result_list.html'
    table_class = tp.tables.FoldChangeResultTable
    table_pagination = True
    filter_class = tp.filters.FoldChangeResultFilter


class SimilarExperimentsSingleTableView(FilteredSingleTableView):
    model = ExperimentCorrelation
    template_name = 'result_list.html'
    table_class = tp.tables.SimilarExperimentsTable
    table_pagination = True
    filter_class = tp.filters.SimilarExperimentsFilter


class ToxicologyResultsSingleTableView(FilteredSingleTableView):
    model = ToxicologyResult
    template_name = 'result_list.html'
    table_class = tp.tables.ToxicologyResultsTable
    table_pagination = True
    filter_class = tp.filters.ToxicologyResultsFilter

