/*

Solution to problem whereby genesets are not clickable.  Jeff just raised the boost threshold.  Here's the correspondence
with HighSoft

Hi Jeff,

      Thank you for using Highcharts.

      You have set boostThreshold to a relatively small number. When running a boosted chart the point click is not respected. The problem is reported here: https://github.com/highcharts/highcharts/issues/4569
      The workaround with halo will not work for the heatmap, because the series doesn't have it. Even adding the marker will not resolve the problem because the lack of marker is needed for the series to draw points correctly.

      Some custom code will have to be added to enable markers for a boosted chart: http://jsfiddle.net/BlackLabel/q5rq7vbh/ Please note that the same code will not work for a chart that is not using boost module.

      Please let us know if you have any more questions.

Best Regards,
Kacper Madej

 */

Highcharts.setOptions({
  plotOptions: {
    heatmap: {
    	//borrow from line
      marker: {
      	enabled: false,
        "lineWidth": 0,
        "radius": 4,
        "states": {
          "normal": {
            "animation": false
          },
          "hover": {
            "animation": false,
            "enabled": true,
            "radiusPlus": 0,
            "lineWidthPlus": 0,
            halo: {
              size: 10,
              opacity: 0.25
            }
          },
          "select": {
            "fillColor": "#cccccc",
            "lineColor": "#000000",
            "lineWidth": 2
          }
        }
      }
    }
  }
});
// Define a custom symbol path
Highcharts.SVGRenderer.prototype.symbols.cross = function (x, y, w, h) {
  	var shapeArgs = h.shapeArgs;
    //get real size
    w = shapeArgs.width;
    h = shapeArgs.height;
    //center
    y -= h/2 - 4;
    return ['M', x, y, 'L', x, y + h, 'L', x + w, y + h, 'L', x + w, y, 'z'];
};
if (Highcharts.VMLRenderer) {
    Highcharts.VMLRenderer.prototype.symbols.cross = Highcharts.SVGRenderer.prototype.symbols.cross;
}

Highcharts.seriesTypes.heatmap.prototype.symbol = 'cross';

//markerAttribs
Highcharts.seriesTypes.heatmap.prototype.markerAttribs = function(point, state){
	var ret = Highcharts.Series.prototype.markerAttribs.call(this, point, state);
  ret.height = point;
  return ret;
}

var options = {

  chart: {
    type: 'heatmap',
    zoomType: 'x',
    marginTop: 40,
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
    labels: {
      step: 1
    }, // seems to be necessary to prevent bunched up Y-axis values
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
    boostThreshold: 1,
    borderWidth: 0,
    nullColor: '#EFEFEF',
    tooltip: {
      headerFormat: '{response.restype}<br/>',
      pointFormat: '{point.feat} <b>{point.value}</b> {point.detail}'
    },
    turboThreshold: Number.MAX_VALUE,
    point: {
      events: {
        click: function(ev) {
          console.log('geneDrillDown(' + ev.point.feat + ',' + ev.point.feat_id + ')');
          console.log(response.data.length);
        }
      }
    },
  }]
};

console.log(response.data.length);
var chart = new Highcharts.chart('viz_container', options);
