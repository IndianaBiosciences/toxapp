/**
 * Created by Jeff Sutherland on 1/10/2018.
 */


$(function () {

  var makeHeatmap = function() {

    console.log('Making the heatmap')
    $('#viz_container').removeClass('hidden');
    $('#hide_viz').removeClass('hidden');
    $('#viz_loading').addClass('loader');

    $.getJSON('http://127.0.0.1:8000/heatmap_json', function (response) {

      sessionStorage.setItem('Ctox_viz_on', 1);

      if(response.empty_dataset) {

        // not changing the sessionStorage status, so next refresh with data will put the chart back
        $('#viz_error').text('No data, nothing to show')
        $('#viz_error').removeClass('hidden')
        $('#viz_container').addClass('hidden');
        $('#hide_viz').addClass('hidden');
        $('#viz_loading').removeClass('loader');

      } else {

        var options = {

          chart: {
            type: 'heatmap'
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
            boostThreshold: 100,
            borderWidth: 0,
            nullColor: '#EFEFEF',
            tooltip: {
              headerFormat: '{response.restype}<br/>',
              pointFormat: '{point.feat} <b>{point.value}</b> {point.detail}'
            },
            turboThreshold: Number.MAX_VALUE // #3404, remove after 4.0.5 release
          }]
        };
        var chart = new Highcharts.chart('viz_container', options);
        $('#viz_loading').removeClass('loader');
      }
    });
  };

  $('#show_viz').on('click', function () {
    makeHeatmap();
  });

  $('#hide_viz').on('click', function () {
    $('#viz_container').addClass('hidden');
    sessionStorage.removeItem('Ctox_viz_on');
  });


  if (sessionStorage.getItem('Ctox_viz_on')) {
    console.log("visualization was on page load");
    makeHeatmap()
  }

});
