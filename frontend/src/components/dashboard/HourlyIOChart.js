import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import formatCETDate from '../common/formatCETDate';

// Import Chart.js components conditionally
let Line;
let ChartJS;
let zoomPlugin;
let chartComponents = false;

try {
  const chartjs = require('chart.js');
  ChartJS = chartjs.Chart;
  const { CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } = chartjs;
  
  // Try to register base components first
  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
  );
  
  // Import react-chartjs-2
  Line = require('react-chartjs-2').Line;
  
  // Set flag that basic components are available
  chartComponents = true;
  
  // Try to import zoom plugin separately
  try {
    zoomPlugin = require('chartjs-plugin-zoom').default;
    ChartJS.register(zoomPlugin);
  } catch (e) {
    console.warn('Zoom plugin not available:', e);
  }
} catch (e) {
  console.error('Error initializing chart components:', e);
}

const HourlyIOChart = () => {
  const [timeData, setTimeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const chartRef = React.useRef(null);

  useEffect(() => {
    const fetchTimeData = async () => {
      try {
        setLoading(true);
        const data = await api.getTimeUsage();
        setTimeData(data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching time usage data:', error);
        setError(error.message || 'Failed to fetch time usage data');
        setLoading(false);
      }
    };

    fetchTimeData();
  }, []);

  const handleResetZoom = () => {
    if (chartRef && chartRef.current) {
      chartRef.current.resetZoom();
    }
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    return formatCETDate(timestamp);
  };

  // Prepare chart data from time series
  const prepareChartData = () => {
    if (!timeData || !timeData.time_series || timeData.time_series.length === 0) {
      return null;
    }

    // Sort time series by timestamp
    const sortedData = [...timeData.time_series].sort((a, b) => 
      new Date(a.timestamp) - new Date(b.timestamp)
    );

    return {
      labels: sortedData.map(item => formatTimestamp(item.timestamp)),
      datasets: [
        {
          label: 'IO Operations',
          data: sortedData.map(item => item.total_operations),
          fill: false,
          borderColor: '#3498db',
          backgroundColor: 'rgba(52, 152, 219, 0.2)',
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 6,
          tension: 0.1
        },
        {
          label: 'Active Users',
          data: sortedData.map(item => item.active_users * 100), // Scale for visibility
          fill: false,
          borderColor: '#2ecc71',
          backgroundColor: 'rgba(46, 204, 113, 0.2)',
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 6,
          tension: 0.1,
          yAxisID: 'y1'
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'IO Operations Over Time'
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            if (context.dataset.label === 'Active Users') {
              return `Active Users: ${context.raw / 100}`; // Descale for display
            }
            return `${context.dataset.label}: ${context.raw}`;
          }
        }
      },
      zoom: {
        pan: {
          enabled: true,
          mode: 'x',
        },
        zoom: {
          wheel: {
            enabled: true,
          },
          mode: 'x',
        },
        limits: {
          x: {min: 'original', max: 'original'},
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Operations'
        },
        ticks: {
          precision: 0
        }
      },
      y1: {
        beginAtZero: true,
        position: 'right',
        title: {
          display: true,
          text: 'Active Users'
        },
        grid: {
          drawOnChartArea: false,
        },
        ticks: {
          precision: 0,
          callback: function(value) {
            return value / 100; // Descale for display
          }
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!chartComponents) {
    return (
      <div className="card">
        <div className="card-header">
          <h3>IO Usage Over Time</h3>
        </div>
        <div className="card-body">
          <ErrorMessage message="Chart components could not be loaded. Please make sure all dependencies are installed." />
          <p className="text-center">
            Required packages: chart.js, react-chartjs-2, chartjs-plugin-zoom
          </p>
        </div>
      </div>
    );
  }
  
  const chartData = prepareChartData();
  if (!chartData) return <ErrorMessage message="No time series data available" />;

  // Create a simplified version of the chart without zoom if the plugin isn't available
  const hasZoomPlugin = typeof zoomPlugin !== 'undefined';
  
  // Modify options based on available plugins
  const finalChartOptions = {
    ...chartOptions,
    plugins: {
      ...chartOptions.plugins,
      zoom: hasZoomPlugin ? chartOptions.plugins.zoom : undefined
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>IO Usage Over Time</h3>
        {hasZoomPlugin && (
          <button className="btn btn-sm" onClick={handleResetZoom}>Reset Zoom</button>
        )}
      </div>
      <div className="card-body">
        <div className="chart-container" style={{ height: '400px' }}>
          <Line 
            ref={chartRef}
            data={chartData} 
            options={finalChartOptions} 
          />
        </div>
        {hasZoomPlugin && (
          <div className="chart-help">
            <p><small>
              <strong>Tip:</strong> Use mouse wheel to zoom in/out on the X-axis. 
              Hold CTRL and drag to pan the view.
            </small></p>
          </div>
        )}
      </div>
    </div>
  );
};

export default HourlyIOChart;