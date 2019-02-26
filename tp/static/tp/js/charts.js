/**
 * JS functions to support results visualizations on result_list.html
 */
//gets all indexes in array with input value
function getAllIndexes(arr, val) {
    var indexes = [], i;
    for(i = 0; i < arr.length; i++)
        if (arr[i] === val)
            indexes.push(i);
    return indexes;
}
//creates a unique array of items in a 2d array
function multiDimensionalUnique(arr) {
    var uniques = [];
    var itemsFound = {};
    for(var i = 0, l = arr.length; i < l; i++) {
        var stringified = JSON.stringify(arr[i]);
        if(itemsFound[stringified]) { continue; }
        uniques.push(arr[i]);
        itemsFound[stringified] = true;
    }
    return uniques;
}



$(function () {

    var makeHeatmap = function() {
        var w = Math.max($('#viz_container.viz_container').width())*.9;
        var h = Math.max($('#viz_container.viz_container').height())*.9;
        var incl_all = $('input[name=incl_all]:checked').val();
        var cluster = $('input[name=cluster]:checked').val();
        var url = '/heatmap_json/?incl_all=' + incl_all + '&cluster=' + cluster;

        $.getJSON(url, function (response) {


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
                        height: h,
                        // need a large value to accomodate the long feature labels and color key
                        // Jeff had lots of problems with bunched y-axis labels until forced container to
                        // have a minimum height of 350 pixels
                        // Update - problem appears again when going to min height of 700 for the other charts
                        // TODO - need some guidance here, may not work well with say 50+ experiments in the heatmap ...
                        // solution for now is to set height to 40% above, which worked fine for 1-15 experiments
                        // another approach would be to set height to a percentage based on the number of rows (experiments)
                        // in the heatmap - i.e. dynamic calculation right here, say minimum of 20% (one series) or 5 * n_exps + '%'
                        marginBottom: 200,
                        plotBorderWidth: 1
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
                $('#heatmap').addClass('active');
                $('#viz_loading').removeClass('loader');
                $('#incl_all_radio').removeClass('hidden');
                $('#cluster_radio').removeClass('hidden');
                $('#heatmap').removeAttr("disabled");
                $('#mapchart').removeAttr("disabled");
                $('#trellis').removeAttr("disabled");
                $('#treemapchart').removeAttr("disabled");
                $('#barchart').removeAttr("disabled");
                $('#bmdaccum').removeAttr("disabled");
            }
        });
    };

    var makeBarChart = function() {

        var incl_all = $('input[name=incl_all]:checked').val();
        var url = '/barchart_json/?incl_all=' + incl_all;
        $.getJSON(url, function (response) {

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
                        zoomType: 'x'
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
                $('#incl_all_radio').removeClass('hidden');
                $('#heatmap').removeAttr("disabled");
                $('#mapchart').removeAttr("disabled");
                $('#trellis').removeAttr("disabled");
                $('#treemapchart').removeAttr("disabled");
                $('#barchart').removeAttr("disabled");
                $('#bmdaccum').removeAttr("disabled");
                $('#barchart').addClass('active');
            }
        });
    };
    var makeMapChart = function() {
            var w = Math.max($('#viz_container.viz_container').width())*.9;
            if(w >= 500){
            w=500;
            }
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
                    makeHeatmap();

                } else if(!response.image) {

                    $('#hide_viz').addClass('hidden');
                    //$('#viz_section').addClass('hidden');
                    $('#viz_loading').removeClass('loader');
                    $('#viz_error').text('No image available for this result type');
                    $('#viz_error').removeClass('hidden');
                    makeHeatmap();

                } else {

                    var options = {

                        chart: {
                            type: 'bubble',
                            //zoomType: 'xy', //image does not zoom with data; use jquery zoom/pan on div
                            height: '100%',
                            /*
                                current Txg map doesn't need to be any bigger and looks too big otherwise
                                TODO - not sure how this will look on mobile devices, no option to use a percent of the
                                container; may need a div inside a div
                                before, Jeff was changing size of container, but then would need to change back when
                                going to other chart type that needs full width ($('#viz_container').width(500);)
                            */
                            width: w,
                            plotBackgroundImage: '/static/tp/img/' + response.image + '.svg'
                        },
                        boost: {
                            useGPUTranslations: true,
                            usePreAllocated: true
                        },

                        title: {
                            text: response.restype + ' map chart'
                        },

                        legend: {
                            enabled: false
                        },

                        // preset ranges for x and y from 0 to 1000 to match image dims
                        xAxis: {
                            min: 0,
                            max: 1000,
                            visible: false
                        },

                        yAxis: {
                            min: -1000,
                            max: 0,
                            visible: false
                        },

                        tooltip: {
                            headerFormat: '{response.restype}<br/>',
                            pointFormat: 'score {point.val}</b> {point.detail}',
                            followPointer: true
                        },

                        plotOptions: {

                            bubble: {
                                minSize: '1%', // percentage of the smallest of plot width or height
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
                    $('#mapchart').addClass('active');
                    $('#viz_loading').removeClass('loader');
                    $('#heatmap').removeAttr("disabled");
                    $('#mapchart').removeAttr("disabled");
                    $('#trellis').removeAttr("disabled");
                    $('#treemapchart').removeAttr("disabled");
                    $('#barchart').removeAttr("disabled");
                    $('#bmdaccum').removeAttr("disabled");
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
    var makeTrellisChart = function() {
            var w = Math.max($('#viz_container.viz_container').width())*.9;
            if(w >= 500){
            w=500;
            }
            $.getJSON('/trellischart_json',{x_val:$('#x_val').val(), y_val: $('#y_val').val()}, function (response) {

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
                    makeHeatmap();

                } else if(!response.image) {

                    $('#hide_viz').addClass('hidden');
                    //$('#viz_section').addClass('hidden');
                    $('#viz_loading').removeClass('loader');
                    $('#viz_error').text('No image available for this result type');
                    $('#viz_error').removeClass('hidden');
                    makeHeatmap();

                } else {

                times = response.times;
                dosages = response.dosages;
                comp = response.comp;
                respdata = response.namers;
                options = [];
                names = [];
                data2 = [];

                for (x in response.data){
                   names.push(response.data[x]['compound_name']+"-"+String(response.data[x]['time']) + "-"+String(response.data[x]['dose']));
                   //genesets.push(response.data[x]['geneset'].match(/:(.*?):/,'')[1])
                }
                for (y in names){
                    var data = [];

                    for (n in response.data){
                       if(names[y]==(response.data[n]['compound_name']+"-"+String(response.data[n]['time']) + "-"+String(response.data[n]['dose']))){
                           data.push(response.data[n]);
                       }
                    }
                    data2.push(data);

                }
                for(m in respdata){
                     options.push({

                        chart: {
                            type: 'bubble',
                            //zoomType: 'xy', //image does not zoom with data; use jquery zoom/pan on div
                            height: '100%',
                            /*
                                current Txg map doesn't need to be any bigger and looks too big otherwise
                                TODO - not sure how this will look on mobile devices, no option to use a percent of the
                                container; may need a div inside a div
                                before, Jeff was changing size of container, but then would need to change back when
                                going to other chart type that needs full width ($('#viz_container').width(500);)
                            */
                            width: w,
                            plotBackgroundImage: '/static/tp/img/' + response.image + '.svg'
                        },
                        boost: {
                            useGPUTranslations: true,
                            usePreAllocated: true
                        },

                        title: {
                            text: respdata[m]+"days "+' map chart'
                        },

                        legend: {
                            enabled: false
                        },

                        // preset ranges for x and y from 0 to 1000 to match image dims
                        xAxis: {
                            min: 0,
                            max: 1000,
                            visible: false
                        },

                        yAxis: {
                            min: -1000,
                            max: 0,
                            visible: false
                        },

                        tooltip: {
                            headerFormat: '{response.restype}<br/>',
                            pointFormat: 'score {point.val}</b> {point.detail}',
                            followPointer: true
                        },

                        plotOptions: {

                            bubble: {
                                minSize: '1%', // percentage of the smallest of plot width or height
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
                            data: data2[m]
                        }]
                    });
                }
                $('.viz_container').empty();
                write = '';

                // for each item in times create the headers
                if(comp.length > 1){

                var iter = 0;
                var counter = 0;
                write = write + '<table style="border: 1px solid black; padding-left:15px;">';
                write = write + '<tr style="border-bottom: 1px solid black;">';
                while(counter < respdata.length){
                write = write + '<td style="border-right: 1px solid black;" id='+String(respdata[counter]).replace(/\s+/g, '')+'></td>';
                counter = counter +1;

                if (iter==2){
                write = write + '</tr>';
                iter = -1;
                write = write + '<tr style="border-bottom: 1px solid black;">';
                }
                iter = iter +1;
                }
                write = write + '</tr></table>';
                $('.viz_container').append(write);
                }else{


                if(response.x_val == 'Dose'){
                write = write + '<table style="border: 1px solid black; padding-left:15px;">' + '<thead style="border: 1px solid black;">' + '<th style="border-right: 1px solid black;"> Times</th>';
                for(x in dosages){
                    write = write + '<th style="text-align: center; border-right: 1px solid black; width:'+w+'px;">'+dosages[x]+'  </th>';

                }
                write = write + '</thead><tbody>';
                //for each item, create a grid of values
                for (z in comp){
                for(x in times){
                    write = write + '<tr style="border-bottom: 1px solid black;">' + '<td style="border-right: 1px solid black;">'+times[x]+' Days</td>';
                    for (y in dosages){
                        write = write + '<td style="border-right: 1px solid black;" id='+String(String(comp[z])+String(dosages[y])+String(times[x])).replace(/\s+/g, '')+'></td>';
                    }
                    write = write + '</tr>';
                }}
                write = write + '</tbody></table>';
                    $('.viz_container').append(write);
                }else{
                write = write + '<table style="border: 1px solid black; padding-left:15px;">' + '<thead style="border: 1px solid black;">' + '<th style="border-right: 1px solid black;"> Dose</th>';
                for(x in times){
                    write = write + '<th style="text-align: center; border-right: 1px solid black; width:'+w+'px;">'+times[x]+' Days </th>';

                }
                write = write + '</thead><tbody>';
                //for each item, create a grid of values
                for (z in comp){
                for(x in dosages){
                    write = write + '<tr style="border-bottom: 1px solid black;">' + '<td style="border-right: 1px solid black;">'+dosages[x]+'</td>';
                    for (y in times){
                        write = write + '<td style="border-right: 1px solid black;" id='+String(String(comp[z])+String(dosages[x])+String(times[y])).replace(/\s+/g, '')+'></td>';
                    }
                    write = write + '</tr>';
                }}
                write = write + '</tbody></table>';
                    $('.viz_container').append(write);
                    }
                    $('.viz_container').find("highcharts-container ");
                    }
                    for (m in respdata){


                        var chart = new Highcharts.chart(''+String(respdata[m]).replace(/\s+/g, '')+'', options[m]);
                    }
                    $('#mapchart').addClass('active');
                    $('#viz_loading').removeClass('loader');
                    $('#heatmap').removeAttr("disabled");
                    $('#mapchart').removeAttr("disabled");
                    $('#trellis').removeAttr("disabled");
                    $('#treemapchart').removeAttr("disabled");
                    $('#barchart').removeAttr("disabled");
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

    var makeTrellisChart2 = function() {

        $.getJSON('/trellischart_json',{x_val:$('#x_val').val(), y_val: $('#y_val').val()}, function (response) {


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
                makeHeatmap();

            } else if(!response.image) {

                $('#hide_viz').addClass('hidden');
                //$('#viz_section').addClass('hidden');
                $('#viz_loading').removeClass('loader');
                $('#viz_error').text('No image available for this result type');
                $('#viz_error').removeClass('hidden');
                makeHeatmap();

            } else {
                var names = [];
                var splitnames = [];
                var options = [];
                var respdata = [];
                var matches = [];
                var times = [];
                var dosages = [];
                var trials =[];
                var write = "";
                var genesets = [];
                var multiple = 0;
                var title = "";
                var x_val = $('#x_val').val();
                var y_val = $('#y_val').val();

                //for each item in response data create a unique string for each item in trellis
                for (x in response.data){
                   names.push(response.data[x]['compound_name']+"-"+String(response.data[x]['time']) + "-"+String(response.data[x]['dose']));
                   //genesets.push(response.data[x]['geneset'].match(/:(.*?):/,'')[1])
                }

                //create a unique array of items representing each item in trellis
                var names = Array.from( new Set(names));
                //split the names up and put them in splitnames
                for (g in names){
                    var trialname = names[g].split("-")[0];
                    splitnames.push(trialname);
                }
                //for each item in names 2 is a match, push to respdata
                for (y in names){
                    var data = [];
                    matches.push(getAllIndexes(splitnames,names[y].split('-')[0]));
                    for (n in response.data){
                       if(names[y]==(response.data[n]['compound_name']+"-"+String(response.data[n]['time']) + "-"+String(response.data[n]['dose']))){
                           data.push(response.data[n]);
                       }
                    }
                    respdata.push(data);

                }
                //get a list of all corrisponding matches
                matches = multiDimensionalUnique(matches);
                //for each item in matches, push the times and dosages to an array
                for(h in matches){
                    for (y in matches[h]) {
                        times.push(respdata[matches[h][y]][0]['time']);
                       // dosages.push(respdata[matches[h][y]][0]['dose'] +respdata[matches[h][y]][0]['dose_unit'])
                        dosages.push(respdata[matches[h][y]][0]['dose']) //+respdata[matches[h][y]][0]['dose_unit'])
                        trials.push(respdata[matches[h][y]][0]['compound_name'])

                    }
                }
                //create unique arrays for the labels on the x and y axis
                times = Array.from(new Set(times));
                dosages = Array.from(new Set(dosages));
                trials = Array.from(new Set(trials));
                if(trials.length >1){
                    multiple = 1;
                }
                //set w to the width of the document, with some changes to set the width of each trellis dynamically
                if(trials.length == 1){
                    //var w = Math.max(document.documentElement.clientWidth, window.innerWidth || 0)/((times.length+1));
                    var w = $("#viz_section").width()/(times.length+1)
                 }
                else{
                var w = $("#viz_section").width()/((4));


                if(w >= 400){
                    w = 400;}
                }

                //create a unqiue option set for each trellis

                for(m in respdata){
                                if(w >300){
                     title = names[m];
                }
                     options.push( {

                        chart: {
                            type: 'bubble',
                            //zoomType: 'xy', //image does not zoom with data; use jquery zoom/pan on div
                            height: '100%',
                            /*
                                current Txg map doesn't need to be any bigger and looks too big otherwise
                                TODO - not sure how this will look on mobile devices, no option to use a percent of the
                                container; may need a div inside a div
                                before, Jeff was changing size of container, but then would need to change back when
                                going to other chart type that needs full width ($('#viz_container').width(500);)
                            */
                            //width: w,
                            plotBackgroundImage: '/static/tp/img/' + response.image + '.svg'
                        },
                        boost: {
                            useGPUTranslations: true,
                            usePreAllocated: true
                        },

                        title: {
                            text: title
                        },

                        legend: {
                            enabled: false
                        },

                        // preset ranges for x and y from 0 to 1000 to match image dims
                        xAxis: {
                            min: 0,
                            max: 1000,
                            visible: false
                        },

                        yAxis: {
                            min: -1000,
                            max: 0,
                            visible: false
                        },

                        tooltip: {
                            headerFormat: '{response.restype}<br/>',
                            pointFormat: 'score {point.val}</b> {point.detail}',
                            followPointer: true
                        },

                        plotOptions: {

                            bubble: {
                                minSize: '1%', // percentage of the smallest of plot width or height
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
                            data: respdata[m]
                        }]
                    });
                }
                if(multiple == 0){
                // sort dosages
                if(y_val=='dose'){
                dosages = dosages.sort();
                }
                else if(y_val =='time'){
                times = times.sort()
                var temp = dosages;
                dosages = times;
                times = temp;

                }

                //empty the viz_container
                $('.viz_container').empty();
                //start adding the table values to write

                write = ''
                write = write + '<table style="border: 1px solid black; padding-left:15px;">' + '<thead style="border: 1px solid black;">' + '<th style="border-right: 1px solid black;"> Dosages</th>';
                // for each item in times create the headers
                for(x in times){
                    write = write + '<th style="text-align: center; border-right: 1px solid black; width:'+w+'px;">'+times[x]+' Days </th>';

                }
                write = write + '</thead><tbody>';
                //for each item, create a grid of values
                for(x in dosages){
                    write = write + '<tr style="border-bottom: 1px solid black;">' + '<td style="border-right: 1px solid black;">'+dosages[x]+'</td>';
                    for (y in times){
                        write = write + '<td style="border-right: 1px solid black;" id='+String(dosages[x])+String(times[y])+'></td>';
                    }
                    write = write + '</tr>';
                }
                write = write + '</tbody></table>';
                   }
                   else{
                   $('.viz_container').empty();
                   write = '';
                   write = write + '<table style="border: 1px solid black; padding-left:15px;"><tbody>';
                   write = write + '<tr style="border-bottom: 1px solid black;">'
                   for (item in respdata){
                    write = write + '<td style="border-right: 1px solid black; width:'+w+'px; " id='+String(respdata[item][0]['dose'])+String(respdata[item][0]['dose_unit'])+String(respdata[item][0]['time'])+'></td>';
                    if(((item +1) % 3)==0){
                    write = write + '</tr><tr style="border-bottom: 1px solid black;">';
                    }
                   }
                   }
                //append the items to the viz_container
                $('.viz_container').append(write);

                //for each item in matches 2d array, append each chart to its corrisponding values in the table
                for(h in matches){
                    for (y in matches[h]){
                        //var chart = new Highcharts.chart(''+String(respdata[matches[h][y]][0]['dose'])+String(respdata[matches[h][y]][0]['dose_unit'])+ String(respdata[matches[h][y]][0]['time'])+'', options[matches[h][y]]);
                        if(x_val == 'time'){
                        var chart = new Highcharts.chart(''+String(respdata[matches[h][y]][0]['dose'])+ String(respdata[matches[h][y]][0]['time'])+'', options[matches[h][y]]);
                        }else{
                        var chart = new Highcharts.chart(''+String(respdata[matches[h][y]][0]['time'])+ String(respdata[matches[h][y]][0]['dose'])+'', options[matches[h][y]]);

                        }
                    }
                }
                $('#viz_loading').removeClass('loader');
                $('#heatmap').removeAttr("disabled");
                $('#mapchart').removeAttr("disabled");
                $('#trellis').removeAttr("disabled");
                $('#treemapchart').removeAttr("disabled");
                $('#barchart').removeAttr("disabled");
                $('#bmdaccum').removeAttr("disabled");
                $('#trellis').addClass('active');
                // there's no need for the pan-zoom functionality for other charts where highcharts zooming works natively
                $('#zoom_buttons').removeClass('hidden');

                var $section = $('#viz_section');
                $section.find('.panzoom').panzoom({
                    $set: $section.find('.panzoom > table>tbody>tr>td>div'),
                    $zoomIn: $section.find('.zoom-in'),
                    $zoomOut: $section.find('.zoom-out'),
                    $reset: $section.find('.reset'),
                    panOnlyWhenZoomed: true,
                    minScale: 1
                });
            }
        });
    };

    var makeTreeMapChart = function() {

        $.getJSON('/treemap_json', function (response) {

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
                makeHeatmap();

            } else {

                var options = {

                    title: {
                        text: 'treemap chart'
                    },

                    tooltip: {
                        pointFormat: '{point.id} {point.value} {point.toolTip}',
                    },

                    colorAxis: {
                        stops: [
                          [0, '#3060cf'],
                          [0.5, '#ffffff'],
                          [1, '#c4463a']
                        ],
                        min: -15,
                        max: 15,
                    },

                    series: [{
                        type: 'treemap',
                        layoutAlgorithm: 'squarified',
                        allowDrillToNode: true,
                        animationLimit: 1000,
                        dataLabels: {
                            enabled: false
                        },
                        levelIsConstant: false,
                        levels: [{
                            level: 1,
                            dataLabels: {
                                enabled: true
                            },
                            borderWidth: 3
                        }],
                        data: response.data
                    }],
                };

                var chart = new Highcharts.chart('viz_container', options);
                $('#viz_loading').removeClass('loader');
                $('#heatmap').removeAttr("disabled");
                $('#mapchart').removeAttr("disabled");
                $('#trellis').removeAttr("disabled");
                $('#treemapchart').removeAttr("disabled");
                $('#barchart').removeAttr("disabled");
                $('#bmdaccum').removeAttr("disabled");
                $('#treemapchart').addClass('active');
            }
        });
    };

    var makeBMDAccumulationChart = function() {

        var incl_all = $('input[name=incl_all]:checked').val();
        var url = '/bmd_accumulation_json/';
        $.getJSON(url, function (response) {

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
                        type: 'scatter',
                        zoomType: 'xy'
                    },
                    boost: {
                        useGPUTranslations: true
                    },
                    title: {
                        text: 'BMD median accumulation plot'
                    },
                    xAxis: {
                        title: {
                            enabled: true,
                            text: 'BMD median'
                        },
                        startOnTick: true,
                        endOnTick: true,
                        showLastLabel: true,
                        type: 'logarithmic'
                    },
                    yAxis: {
                        title: {
                            text: 'Accumulation'
                        }
                    },
                    plotOptions: {
                        series: {
                            lineWidth: 1,
                            boostThreshold: 5000,
                            turboThreshold: 10000
                        },
                        scatter: {
                            marker: {
                                radius: 5,
                                states: {
                                    hover: {
                                        enabled: true,
                                        lineColor: 'rgb(100,100,100)'
                                    }
                                }
                            },
                            states: {
                                hover: {
                                    marker: {
                                        enabled: false
                                    }
                                }
                            },
                            tooltip: {
                                headerFormat: '<b>{series.name}</b><br>',
                                pointFormat: '{point.detail}'
                            }
                        }
                    },

                    series: response.series
                };

                var chart = new Highcharts.chart('viz_container', options);
                $('#viz_loading').removeClass('loader');
                $('#heatmap').removeAttr("disabled");
                $('#mapchart').removeAttr("disabled");
                $('#trellis').removeAttr("disabled");
                $('#treemapchart').removeAttr("disabled");
                $('#barchart').removeAttr("disabled");
                $('#bmdaccum').removeAttr("disabled");
                $('#bmdaccum').addClass('active');
            }
        });
    };

    var makePlot = function() {

    var w = $('thead').width();

            $('#viz_section').width(w);
                    $('#heatmap').attr("disabled", "disabled");


        $('#mapchart').attr("disabled", "disabled");
        $('#trellis').attr("disabled", "disabled");
        $('#treemapchart').attr("disabled", "disabled");
        $('#barchart').attr("disabled", "disabled");
        $('#bmdaccum').attr("disabled", "disabled");
        $('#viz_error').addClass('hidden');
        $('#viz_loading').addClass('loader');
        $('#genedrilldown').addClass('hidden');

        if (!sessionStorage.getItem('viz_type')) {
            // default to heatmap
            sessionStorage.setItem('viz_type', 'heatmap');
        }

        var type = sessionStorage.getItem('viz_type');
        console.log('Plot type is', type)
        if (type === 'heatmap') {
            $('#zoom_buttons').addClass('hidden');
            makeHeatmap();
        } else if (type === 'mapchart') {
            $('#incl_all_radio').addClass('hidden');
            $('#cluster_radio').addClass('hidden');
            makeMapChart();
        } else if (type === 'treemapchart') {
            $('#incl_all_radio').addClass('hidden');
            $('#cluster_radio').addClass('hidden');
            makeTreeMapChart();
        } else if (type === 'barchart') {
            $('#zoom_buttons').addClass('hidden');
            $('#cluster_radio').addClass('hidden');
            makeBarChart();
        } else if(type === 'trellis') {
            $('#incl_all_radio').addClass('hidden');
            $('#cluster_radio').addClass('hidden');
            makeTrellisChart();
        } else if(type === 'bmdaccum') {
            $('#incl_all_radio').addClass('hidden');
            $('#cluster_radio').addClass('hidden');
            makeBMDAccumulationChart();
        } else {
            console.log('Chart of type ' + type.toString() + ' not supported');
        }
    };

    // show currently selected geneset and button for retrieving gene level view
    var geneDrillDown = function(geneset, id) {
        $('#genedrilldown').removeClass('hidden');
        $('#selected_geneset').text(geneset);
        var url = $('#genefetch').attr('href');
        url = url.replace('999999', id);
        $('#genefetch').attr('href', url)
    };

    $('#genefetch').on('click', function () {
        $('#mapchart').addClass('hidden');
        $('#treemapchart').addClass('hidden');
        sessionStorage.setItem('viz_type', 'heatmap');
        // going to a heatmap and not navigating through results summary; explicitly disable
        sessionStorage.removeItem('map_ok');
        sessionStorage.removeItem('treemap_ok');
        //e.preventDefault()
    });

    $('#show_viz').on('click', function () {
        if (! $(this).hasClass('disabled')) {
            $(this).addClass('hidden');
            $('#viz_section').removeClass('hidden');
            $('#hide_viz').removeClass('hidden');
            sessionStorage.setItem('Ctox_viz_on', '1');
            makePlot()
        }
    });

    $('#hide_viz').on('click', function () {
        $(this).addClass('hidden');
        $('#viz_section').addClass('hidden');
        $('#show_viz').removeClass('hidden');
        $('#genedrilldown').addClass('hidden');
        sessionStorage.removeItem('Ctox_viz_on');
    });

    $('#heatmap').on('click', function () {

        var current_type = sessionStorage.getItem('viz_type');
        sessionStorage.setItem('viz_type', 'heatmap');
        // no need to make the plot if already on the selected type
        if (!current_type || current_type !== 'heatmap') {
            makePlot()
        }
    });

    $('#mapchart').on('click', function () {

        var current_type = sessionStorage.getItem('viz_type');
        sessionStorage.setItem('viz_type', 'mapchart');
        // no need to make the plot if already on the selected type
        if (!current_type || current_type !== 'mapchart') {
            makePlot()
        }
    });

    $('#trellis').on('click', function () {

        var current_type = sessionStorage.getItem('viz_type');
        sessionStorage.setItem('viz_type', 'trellis');

        // no need to make the plot if already on the selected type
        if (!current_type || current_type !== 'trellis') {
            makePlot()
        }
    });
    $('#Submit').on('click', function () {

        var current_type = sessionStorage.getItem('viz_type');
        sessionStorage.setItem('viz_type', 'trellis');

        // no need to make the plot if already on the selected type

            makePlot()

    });
    $('#treemapchart').on('click', function () {

        var current_type = sessionStorage.getItem('viz_type');
        sessionStorage.setItem('viz_type', 'treemapchart');
        // no need to make the plot if already on the selected type
        // JS Note - why a check on treemap_ok here but not other result-specific charts
        if (!current_type || current_type !== 'treemapchart' && sessionStorage.getItem('treemap_ok')) {
            makePlot()
        }else{
            // JS Note - looks like added by Austin; why?
            sessionStorage.setItem('viz_type', 'barchart');
        }
    });

    $('#barchart').on('click', function () {

        var current_type = sessionStorage.getItem('viz_type');
        sessionStorage.setItem('viz_type', 'barchart');
        // no need to make the plot if already on the selected type
        if (!current_type || current_type !== 'barchart') {
            makePlot()
        }
    });

    $('#bmdaccum').on('click', function () {

        var current_type = sessionStorage.getItem('viz_type');
        sessionStorage.setItem('viz_type', 'bmdaccum');
        // no need to make the plot if already on the selected type
        if (!current_type || current_type !== 'bmdaccum') {
            makePlot()
        }
    });

    // if clustering set to 'yes', then set 'show all values' to 'yes'
    $('input[type=radio][name=cluster]').change(function () {
        if (this.value === '1') {
            $('input[type=radio][name=incl_all]:eq(1)').prop('checked', true);
        }
    });

    // render the plot again if changing options
    $('#chart_options input:radio').change(function () {
        makePlot();
    });

    // used when refreshing the page on filtering criteria - don't keep hidding the graph
    if (sessionStorage.getItem('Ctox_viz_on') && !$('#show_viz').hasClass('disabled')) {
        $('#show_viz').addClass('hidden');
        $('#viz_section').removeClass('hidden');
        $('#hide_viz').removeClass('hidden');
        makePlot()
    }


    if (sessionStorage.getItem('map_ok')) {
        // show the mapchart button when appropriate
        $('#mapchart').removeClass('hidden');
        $('#trellis').removeClass('hidden');
    } else {
        // after viewing a mapchart and going to other types, set the selected type
        // to something valid
        sessionStorage.setItem('viz_type', 'heatmap');
    }

    if (sessionStorage.getItem('treemap_ok')) {
        // show the treemap button when appropriate
        $('#treemapchart').removeClass('hidden')
    } else {
        // after viewing a treemap and going to other types, set the selected type
        // to something valid
        $('#treemapchart').addClass('hidden');
        sessionStorage.setItem('viz_type', 'heatmap');
    }

    if (sessionStorage.getItem('bmd_ok')) {
        // show the treemap button when appropriate
        console.log('Viewing BMD results');
        $('#heatmap').addClass('hidden');
        $('#barchart').addClass('hidden');
        $('#mapchart').addClass('hidden');
        $('#trellis').addClass('hidden');
        $('#treemapchart').addClass('hidden');
        $('#bmdaccum').removeClass('hidden');
        // unlike other result types, heatmap is not a suitable default; currently only viable plot is bmdaccum
        // set this explicilty to avoid defaulting to heatmap in makePlot
        sessionStorage.setItem('viz_type', 'bmdaccum');
    } else {
        // after viewing a bmd accum plot and going to other types, set the selected type
        // to something valid
        $('#bmdaccum').addClass('hidden');
        sessionStorage.setItem('viz_type', 'heatmap');
    }

});
