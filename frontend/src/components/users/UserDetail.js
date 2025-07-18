import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
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
import UserCurrentUsage from './UserCurrentUsage';
import UserJobs from './UserJobs';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const UserDetail = () => {
  const { username } = useParams();
  const [userData, setUserData] = useState(null);
  const [timeData, setTimeData] = useState([]);
  const [currentUsage, setCurrentUsage] = useState(null);
  const [runningJobs, setRunningJobs] = useState([]);
  const [jobHistory, setJobHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [thesisInfo, setThesisInfo] = useState(null);
  const [thesisError, setThesisError] = useState(null);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);
        
        // Fetch user details
        const data = await api.getUserUsage(username);
        setUserData(data);
        
        // Fetch time stats
        const timeStats = await api.getUserTimeStats(username);
        setTimeData(timeStats);

        // Fetch current usage, running jobs, and job history
        const overviewData = await api.getUserOverview(username);
        setCurrentUsage(overviewData.currentUsage);
        setRunningJobs(overviewData.runningJobs);
        setJobHistory(overviewData.jobHistory);
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching user data:', error);
        setError(error.message || `Failed to fetch data for user ${username}`);
        setLoading(false);
      }
    };

    fetchUserData();
  }, [username]);

  useEffect(() => {
    const fetchThesisInfo = async () => {
      try {
        const data = await api.getUserThesisSupervisors(username);
        setThesisInfo(data);
        setThesisError(null);
      } catch (err) {
        setThesisInfo(null);
        setThesisError('No thesis information');
      }
    };
    fetchThesisInfo();
  }, [username]);

  // Format date for chart display
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Prepare chart data
  const prepareChartData = () => {
    const labels = timeData.map(item => formatDate(item.timestamp));
    const operations = timeData.map(item => item.total_operations);
    
    return {
      labels,
      datasets: [
        {
          label: 'IO Operations',
          data: operations,
          fill: false,
          backgroundColor: '#3498db',
          borderColor: '#3498db',
          tension: 0.1
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
        text: `IO Operations Over Time for ${username}`
      },
      tooltip: {
        callbacks: {
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
  if (!userData) return <ErrorMessage message={`User ${username} not found`} />;

  return (
    <div className="user-detail-container">
      {/* Thesis and Supervisor Info at the top */}
      <div style={{ marginBottom: 20 }}>
        {thesisInfo && thesisInfo.length > 0 ? (
          <div style={{ background: '#e3f0ff', color: '#155fa0', borderRadius: 8, padding: 16, border: '1px solid #b6d4fe' }}>
            <strong>Thesis Information</strong>
            {thesisInfo.map((thesis, idx) => (
              <div key={idx} style={{ marginTop: 8 }}>
                <div><strong>Title:</strong> {thesis.thesis_title}</div>
                <div><strong>Semester:</strong> {thesis.semester}</div>
                <div><strong>Supervisors:</strong> {thesis.supervisors && thesis.supervisors.length > 0 ? thesis.supervisors.join(', ') : '-'}</div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ background: '#f3f3f3', color: '#555', borderRadius: 8, padding: 16, border: '1px solid #ddd' }}>
            No thesis information
          </div>
        )}
      </div>
      <div className="page-header">
        <h2 className="page-title">User Details: {username}</h2>
        <Link to="/users" className="btn btn-secondary">Back to Users</Link>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>User Information</h3>
        </div>
        <div className="card-body">
          {userData.image_url && (
            <div className="user-image-container">
              <img 
                src={userData.image_url} 
                alt={userData.full_name || userData.username} 
                className="user-profile-image"
              />
            </div>
          )}
          <div className="table-container">
            <table className="table">
              <tbody>
                <tr>
                  <th>Username</th>
                  <td>{userData.username}</td>
                </tr>
                {userData.full_name && (
                  <tr>
                    <th>Name</th>
                    <td>{userData.full_name}</td>
                  </tr>
                )}
                <tr>
                  <th>Role</th>
                  <td>
                    {userData.user_role && (
                      <span className={`badge badge-${userData.user_role.toLowerCase()}`}>
                        {userData.user_role}
                      </span>
                    )}
                  </td>
                </tr>
                {userData.title && (
                  <tr>
                    <th>Position</th>
                    <td>{userData.title}</td>
                  </tr>
                )}
                <tr>
                  <th>Affiliation</th>
                  <td>{userData.user_affiliation || '-'}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>IO Usage Over Time</h3>
        </div>
        <div className="card-body">
          {timeData.length > 0 ? (
            <div className="chart-container">
              <Line data={prepareChartData()} options={chartOptions} />
            </div>
          ) : (
            <p>No time data available for this user.</p>
          )}
        </div>
      </div>

      {userData.machines && userData.machines.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3>Machines Used</h3>
          </div>
          <div className="card-body">
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Machine Name</th>
                    <th>Type</th>
                    <th>Sessions</th>
                  </tr>
                </thead>
                <tbody>
                  {userData.machines.map((machine, index) => (
                    <tr key={index}>
                      <td>{machine.machine_name}</td>
                      <td>{machine.machine_type}</td>
                      <td>{machine.session_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {userData.io_distribution && userData.io_distribution.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3>IO Size Distribution</h3>
          </div>
          <div className="card-body">
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Size Range</th>
                    <th>Operation Count</th>
                  </tr>
                </thead>
                <tbody>
                  {userData.io_distribution.map((item, index) => (
                    <tr key={index}>
                      <td>{item.display_text}</td>
                      <td>{item.total_operations}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Current Resource Usage */}
      <div className="card">
        <div className="card-header">
          <h3>Current Resource Usage</h3>
        </div>
        <div className="card-body">
          <UserCurrentUsage usage={currentUsage} />
        </div>
      </div>

      {/* Running Jobs */}
      <div className="card">
        <div className="card-header">
          <h3>Running Jobs</h3>
        </div>
        <div className="card-body">
          <UserJobs jobs={runningJobs} isRunningJobs={true} />
        </div>
      </div>

      {/* Job History */}
      <div className="card">
        <div className="card-header">
          <h3>Job History</h3>
        </div>
        <div className="card-body">
          <UserJobs jobs={jobHistory} isRunningJobs={false} />
        </div>
      </div>
    </div>
  );
};

export default UserDetail;

