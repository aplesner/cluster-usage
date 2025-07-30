import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import formatCETDate from '../common/formatCETDate';

// Register Chart.js components - same as in UserDetail.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const SimpleIOChart = () => {
  const [timeData, setTimeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  // Format date for chart display - same approach as UserDetail.js
  const formatDate = (dateString) => {
    return formatCETDate(dateString, { month: 'short', day: 'numeric' });
  };

  // Prepare chart data
  const prepareChartData = () => {
    if (!timeData || !timeData.time_series || timeData.time_series.length === 0) {
      return null;
    }

    // Sort time series by timestamp
    const sortedData = [...timeData.time_series].sort((a, b) => 
      new Date(a.timestamp) - new Date(b.timestamp)
    );

    const labels = sortedData.map(item => formatDate(item.timestamp));
    const operations = sortedData.map(item => item.total_operations);
    
    // Store original timestamps in an additional array for tooltips
    const timestamps = sortedData.map(item => item.timestamp);
    
    return {
      labels,
      datasets: [
        {
          label: 'IO Operations',
          data: operations,
          fill: false,
          backgroundColor: '#3498db',
          borderColor: '#3498db',
          borderWidth: 2,
          tension: 0.1,
          // Store timestamps as custom property for tooltip access
          timestamps: timestamps
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
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
          title: function(context) {
            // Get the timestamp from our custom property
            const dataIndex = context[0].dataIndex;
            const timestamp = context[0].dataset.timestamps[dataIndex];
            
            // Format with hour precision
            const date = new Date(timestamp);
            return date.toLocaleString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            });
          },
          label: function(context) {
            return `Operations: ${context.parsed.y}`;
          }
        }
      }
    },
    scales: {
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
      x: {
        title: {
          display: true,
          text: 'Time'
        }
      }
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  
  const chartData = prepareChartData();
  if (!chartData) return <ErrorMessage message="No time series data available" />;

  return (
    <div className="card">
      <div className="card-header">
        <h3>IO Usage Over Time</h3>
      </div>
      <div className="card-body">
        <div className="chart-container">
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
};

export default SimpleIOChart;