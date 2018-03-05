/**
 * JS functions to support results visualizations on result_list.html
 */


$(function () {

    var makeHeatmap = function() {

        $.getJSON('/heatmap_json', function (response) {

            if(response.empty_dataset) {

                // not changing the sessionStorage status, so next refresh with data will put the chart back
                $('#hide_viz').addClass('hidden');
                $('#viz_error').text('No data, nothing to show');
                $('#viz_error').removeClass('hidden');
                $('#viz_section').addClass('hidden');
                $('#viz_loading').removeClass('loader');

            } else {

                // per https://www.highcharts.com/docs/working-with-data/custom-preprocessing
                // since we are getting external json file, load data into options before
                // chart creation to avoid drawing chart twice
                var options = {

                    chart: {
                        type: 'heatmap',
                        zoomType: 'x',
                        marginTop: 40,
                        // need a large value to accomodate the long feature labels and color key
                        // Jeff had lots of problems with bunched y-axis labels until forced container to
                        // have a minimum height of 350 pixels
                        marginBottom: 200,
                        plotBorderWidth: 1,
                    },

                    boost: {
                        useGPUTranslations: true
                    },

                    title: {
                        text: response.restype + ' heatmap',
                        align: 'left'
                    },

                    xAxis: {
                        title: {
                            text: response.scale
                        },
                        minPadding: 0,
                        maxPadding: 0,
                        categories: response.x_vals
                    },

                    yAxis: {
                        title: {
                            text: 'experiments'
                        },
                        minPadding: 0,
                        maxPadding: 0,
                        labels: {step: 1}, // seems to be necessary to prevent bunched up Y-axis values
                        categories: response.y_vals
                    },

                    colorAxis: {
                        stops: [
                            [0, '#3060cf'],
                            [0.5, '#fffbbc'],
                            [1, '#c4463a']
                        ],
                        min: response.scalemin,
                        max: response.scalemax,
                        startOnTick: true,
                        endOnTick: true,
                        labels: {
                            format: '{value}'
                        }
                    },

                    series: [{
                        data: response.data,
                        cursor: 'pointer',
                        boostThreshold: 10000,
                        borderWidth: 0,
                        nullColor: '#EFEFEF',
                        tooltip: {
                            headerFormat: '{response.restype}<br/>',
                            pointFormat: '{point.feat} <b>{point.value}</b> {point.detail}'
                        },
                        turboThreshold: Number.MAX_VALUE
                    }]
                };

                if (response.drilldown_ok) {
                    options.series[0].events = {
                        click: function (ev) {
                            geneDrillDown(ev.point.feat, ev.point.feat_id);
                        }
                    }
                }

                var chart = new Highcharts.chart('viz_container', options);
                $('#viz_loading').removeClass('loader');
            }
        });
    };

    var makeBarChart = function() {

        $.getJSON('/barchart_json', function (response) {

            if(response.empty_dataset) {

                // not changing the sessionStorage status, so next refresh with data will put the chart back
                $('#hide_viz').addClass('hidden');
                $('#viz_error').text('No data, nothing to show');
                $('#viz_error').removeClass('hidden');
                $('#viz_section').addClass('hidden');
                $('#viz_loading').removeClass('loader');

            } else {

                var options = {

                    chart: {
                        type: 'column',
                        zoomType: 'x',
                    },

                    title: {
                        text: response.restype + ' barchart',
                        align: 'left'
                    },

                    xAxis: {
                        categories: response.categories,
                        labels: {
                            rotation: -45,
                            style: {
                                fontSize: '13px',
                                fontFamily: 'Verdana, sans-serif'
                            }
                        }
                    },

                    yAxis: {
                        title: {
                            text: response.scale
                        }
                    },

                    plotOptions: {
                        series: {
                            stacking: 'normal'
                        }
                    },

                    tooltip: {
                        headerFormat: '{response.restype}<br/>',
                        pointFormat: '{point.feat} <b>{point.y}</b> {point.detail}'
                    },

                    series: response.series
                };

                if (response.drilldown_ok) {
                    options.series[0].events = {
                        click: function (ev) {
                            geneDrillDown(ev.point.feat, ev.point.feat_id);
                        }
                    }
                }

                var chart = new Highcharts.chart('viz_container', options);
                $('#viz_loading').removeClass('loader');
            }
        });
    };


    var makeMapChart = function() {

        // current Txg map doesn't need to be any bigger and looks too big otherwise
        $('#viz_container').width(500);

        $.getJSON('/mapchart_json', function (response) {

            if(response.empty_dataset) {

                // not changing the sessionStorage status, so next refresh with data will put the chart back
                $('#hide_viz').addClass('hidden');
                $('#viz_section').addClass('hidden');
                $('#viz_loading').removeClass('loader');
                $('#viz_error').text('No data, nothing to show');
                $('#viz_error').removeClass('hidden');

            } else if(response.not_applicable) {

                $('#hide_viz').addClass('hidden');
                //$('#viz_section').addClass('hidden');
                sessionStorage.setItem('viz_type', 'heatmap');
                $('#viz_loading').removeClass('loader');
                $('#viz_error').text('map chart not supported for this data type');
                $('#viz_error').removeClass('hidden');

            } else if(!response.image) {

                $('#hide_viz').addClass('hidden');
                //$('#viz_section').addClass('hidden');
                $('#viz_loading').removeClass('loader');
                $('#viz_error').text('No image available for this result type');
                $('#viz_error').removeClass('hidden');

            } else {

                var options = {

                    chart: {
                        type: 'bubble',
                        //zoomType: 'xy', //image does not zoom with data; use jquery zoom/pan on div
                        height: '100%',
                        plotBackgroundImage: '/static/tp/img/' + response.image + '.svg'
                    },
                    boost: {
                        useGPUTranslations: true,
                        usePreAllocated: true
                    },

                    title: {
                        text: response.restype + ' map chart',
                    },

                    legend: {
                        enabled: false
                    },

                    // preset ranges for x and y from 0 to 1000 to match image dims
                    xAxis: {
                        min: 0,
                        max: 1000,
                        visible: false,
                    },

                    yAxis: {
                        min: -1000,
                        max: 0,
                        visible: false,
                    },

                    tooltip: {
                        headerFormat: '{response.restype}<br/>',
                        pointFormat: 'score {point.val}</b> {point.detail}',
                        followPointer: true,
                    },

                    plotOptions: {

                        bubble: {
                            minSize: '0.1%', // percentage of the smallest of plot width or height
                            maxSize: '5%'    // percentage of the smallest of plot width or height
                        },

                        series: {
                            cursor: 'pointer',
                            events: {
                                click: function (ev) {
                                    geneDrillDown(ev.point.geneset, ev.point.geneset_id);
                                }
                            }
                        }
                    },

                    series: [{
                        //colorByPoint: true,
                        data: response.data
                    }]
                };

                var chart = new Highcharts.chart('viz_container', options);
                $('#viz_loading').removeClass('loader');

                // there's no need for the pan-zoom functionality for other charts where highcharts zooming works natively
                $('#zoom_buttons').removeClass('hidden');
                var $section = $('#viz_section');
                $section.find('.panzoom').panzoom({
                    $zoomIn: $section.find('.zoom-in'),
                    $zoomOut: $section.find('.zoom-out'),
                    $reset: $section.find('.reset'),
                    panOnlyWhenZoomed: true,
                    minScale: 1
                });
            }
        });
    };

    var makePlot = function() {

        $('#viz_error').addClass('hidden');
        $('#viz_loading').addClass('loader');
        $('#genedrilldown').addClass('hidden')

        if (!sessionStorage.getItem('viz_type')) {
            // default to heatmap
            sessionStorage.setItem('viz_type', 'heatmap');
        }

        var type = sessionStorage.getItem('viz_type');
        if (type == 'heatmap') {
            makeHeatmap();
        } else if (type == 'mapchart') {
            makeMapChart();
        } else if (type == 'barchart') {
            makeBarChart();
        } else {
            console.log('Chart of type ' + type.toString() + ' not supported');
        }
    };

    // show currently selected geneset and button for retrieving gene level view
    var geneDrillDown = function(geneset, id) {
        $('#genedrilldown').removeClass('hidden')
        $('#selected_geneset').text(geneset)
        var url = $('#genefetch').attr('href');
        url = url.replace('999999', id)
        $('#genefetch').attr('href', url)
    }

    $('#genefetch').on('click', function (e) {
        console.log('clicked')
        $('#mapchart').addClass('hidden')
        sessionStorage.setItem('viz_type', 'heatmap');
        // going to a heatmap and not navigating through results summary; explicitly disable
        sessionStorage.removeItem('map_ok');
        //e.preventDefault()
    });

    $('#show_viz').on('click', function () {
        if (! $(this).hasClass('disabled')) {
            $(this).addClass('hidden')
            $('#viz_section').removeClass('hidden');
            $('#hide_viz').removeClass('hidden');
            // TODO - check whether there's a plot there already, and if so, don't remake it
            sessionStorage.setItem('Ctox_viz_on', '1');
            makePlot()
        }
    });

    $('#hide_viz').on('click', function () {
        $(this).addClass('hidden')
        $('#viz_section').addClass('hidden');
        $('#show_viz').removeClass('hidden');
        $('#genedrilldown').addClass('hidden')
        sessionStorage.removeItem('Ctox_viz_on');
    });

    $('#heatmap').on('click', function () {
        var current_type = sessionStorage.getItem('viz_type');
        sessionStorage.setItem('viz_type', 'heatmap');
        // no need to make the plot if already on the selected type
        if (!current_type || current_type != 'heatmap') {
            makePlot()
        }
    });

    $('#mapchart').on('click', function () {
        var current_type = sessionStorage.getItem('viz_type');
        sessionStorage.setItem('viz_type', 'mapchart');
        // no need to make the plot if already on the selected type
        if (!current_type || current_type != 'mapchart') {
            makePlot()
        }
    });

    $('#barchart').on('click', function () {
        var current_type = sessionStorage.getItem('viz_type');
        sessionStorage.setItem('viz_type', 'barchart');
        // no need to make the plot if already on the selected type
        if (!current_type || current_type != 'barchart') {
            makePlot()
        }
    });

    // used when refreshing the page on filtering criteria - don't keep hidding the graph
    if (sessionStorage.getItem('Ctox_viz_on') && !$('#show_viz').hasClass('disabled')) {
        $('#show_viz').addClass('hidden')
        $('#viz_section').removeClass('hidden');
        $('#hide_viz').removeClass('hidden');
        makePlot()
    }


    if (sessionStorage.getItem('map_ok')) {
        // show the mapchart button when appropriate
        $('#mapchart').removeClass('hidden')
    } else {
        // after viewing a mapchart and going to other types, set the selected type
        // to something valid
        sessionStorage.setItem('viz_type', 'heatmap');
    }

});
