/**
 * Javascript components for toxapp
 */
$(function() {

    // add class loader to div set up to show progress on upload form
    $('form').on('submit', function () {
        $('#uploadIcon').addClass('loader')
    });

    // button to uncheck all boxes
    $('#uncheckButton').on('click', function() {
        $("input[type='checkbox']").prop("checked", false)
    });

    // button to check all boxes
    $('#checkButton').on('click', function() {
        $("input[type='checkbox']").prop("checked", true)
    });

    // enable datepicker from JQuery UI on elements of that class
    $('.datepicker').datepicker();

    // clicking on experiment name in experiment_form.html causes auto-population of name
    $('#experiment_auto_btn').on('click', function () {

        var compound_name = $('#id_compound_name').val()
        var dose = $('#id_dose').val()
        var dose_unit = $('#id_dose_unit').val()
        var time = $('#id_time').val()
        var tissue = $('#id_tissue').val()
        var organism = $('#id_organism').val()
        var gender = $('#id_gender').val()
        var single_repeat_type = $('#id_single_repeat_type').val()

        var expname = ''
        if (compound_name) {
            expname += compound_name.substring(0, 12)
        }

        if (time) {
            expname += '-' + time + 'd'
        }

        if (dose && dose_unit) {
            expname += '-' + dose + dose_unit
        }
        expname += '-' + single_repeat_type
        expname += '-' + tissue.toUpperCase().substr(0, 2) + '-' + organism.toUpperCase().substr(0, 3) + gender

        $('#id_experiment_name').val(expname)
    });

    // when accessing results from the summary page, make sure that the visualization is initially hidden
    $('.reslink').on('click', function () {
        sessionStorage.removeItem('Ctox_viz_on');
    });

    // determine whether to show the mapchart option - for modules / genesets only
    $('.map_ok').on('click', function () {
        sessionStorage.setItem('map_ok', '1');
    });

    // if coming back to the result summary page from a results page, reset the mapchart status
    $('#res_summary_link').on('click', function () {
        sessionStorage.removeItem('map_ok');
    });
    
});
