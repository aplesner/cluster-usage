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
      console.log(`Fetching thesis details for user: ${username}`);
      
      const data = await api.fetchThesisDetails(username);
      
      console.log('Fetched thesis data:', data);

      // Check if data is valid and log it
      if (!data || !data.theses) {
        throw new Error('No thesis details found');
      }
      // Set thesis info state
      setThesisInfo(data.theses);
      setThesisError(null);
      // Log the fetched thesis data for debugging
    } catch (err) {
      console.error('Error fetching thesis info:', err);
      setThesisInfo(null);
      setThesisError('No thesis information available');
    }
  };
  fetchThesisInfo();
}, [username]);

const ThesisInfoDisplay = ({ thesisInfo, thesisError }) => {
  if (thesisError || !thesisInfo || thesisInfo.length === 0) {
    console.warn('No thesis information available or error occurred:', thesisError);
    return (
      <div className="card">
        <div className="card-header">
          <h3>Thesis Information</h3>
        </div>
        <div className="card-body">
          <p>No thesis information available... 123</p>
          {thesisError && <p className="text-danger">{thesisError}</p>}
          {/* Display a message if no thesis information is available */}
          {/* <p>No thesis information available for this user.</p> */}
          <p>No thesis information available for this user. {thesisInfo}</p>
        </div>
      </div>
    );
  }

  // Display thesis information in a table using the `theses` prop
  const allTheses = thesisInfo.map(thesis => ({
    icon_url: thesis.icon_url || '',
    thesis_title: thesis.thesis_title || 'N/A',
    semester: thesis.semester || 'N/A',
    role: thesis.role || 'N/A',
    supervisors: thesis.supervisors || [],
    // If student email is not an array, convert it to an array
    // If student email is an array, use it directly
    student_email: Array.isArray(thesis.student_email) ? thesis.student_email : [thesis.student_email || 'N/A'],
    status: thesis.is_past ? 'Past' : 'Current'
  }));

  return (
    <div className="card">
      <div className="card-header">
        <h3>Thesis Information</h3>
      </div>
      <div className="card-body">
        {allTheses.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th></th>
                  <th>Thesis Title</th>
                  <th>Semester</th>
                  <th>Role</th>
                  <th>Supervisors</th>
                  <th>Student E-mail</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {allTheses.map((thesis, index) => (
                  <tr key={index}>
                    <td>
                      {thesis.icon_url ? (
                        <img src={thesis.icon_url} alt={thesis.thesis_title} className="thesis-icon" />
                      ) : (
                        <div className="thesis-icon-placeholder">No Image</div>
                      )}
                    </td>
                    <td>{thesis.thesis_title}</td>
                    <td>{thesis.semester}</td>
                    <td>{thesis.role}</td>
                    <td>
                      {thesis.supervisors.length > 0 ? (
                        thesis.supervisors.join(', ')
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td>
                      {thesis.student_email.length > 0 ? (
                        thesis.student_email.join(', ')
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td>{thesis.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>No thesis information available for this user.</p>
        )}
      </div>
    </div>
  );
};

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
      <ThesisInfoDisplay thesisInfo={thesisInfo} thesisError={thesisError} />
      
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

