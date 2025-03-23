import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import TopUsersRecent from './TopUsersRecent';

const DashboardHome = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.getStats();
        setStats(data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching stats:', error);
        setError(error.message || 'Failed to fetch dashboard statistics');
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  // Format dates for display
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Format large numbers with commas
  const formatNumber = (num) => {
    if (num === undefined || num === null) return 'N/A';
    return num.toLocaleString();
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="dashboard-container">
      <h2 className="page-title">IO Usage Dashboard</h2>
      
      <div className="card-grid">
        <div className="stat-card">
          <h3 className="stat-label">Total Users</h3>
          <div className="stat-value">{formatNumber(stats?.user_count)}</div>
          <Link to="/users" className="btn">View Users</Link>
        </div>
        
        <div className="stat-card">
          <h3 className="stat-label">Total Machines</h3>
          <div className="stat-value">{formatNumber(stats?.machine_count)}</div>
          <Link to="/machines" className="btn">View Machines</Link>
        </div>
        
        <div className="stat-card">
          <h3 className="stat-label">Total Sessions</h3>
          <div className="stat-value">{formatNumber(stats?.session_count)}</div>
          <Link to="/time" className="btn">Time Analysis</Link>
        </div>
        
        <div className="stat-card">
          <h3 className="stat-label">Total IO Operations</h3>
          <div className="stat-value">{formatNumber(stats?.total_operations)}</div>
          <Link to="/sizes" className="btn">Size Distribution</Link>
        </div>
      </div>
      
      <div className="card">
        <div className="card-header">
          <h3>IO Usage Overview</h3>
        </div>
        <div className="card-body">
          <div className="table-container">
            <table className="table">
              <tbody>
                <tr>
                  <th>First Log Date</th>
                  <td>{formatDate(stats?.min_date)}</td>
                </tr>
                <tr>
                  <th>Latest Log Date</th>
                  <td>{formatDate(stats?.max_date)}</td>
                </tr>
                <tr>
                  <th>Total Log Entries</th>
                  <td>{formatNumber(stats?.log_count)}</td>
                </tr>
                <tr>
                  <th>Total IO Operations</th>
                  <td>{formatNumber(stats?.operation_count)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      {/* Top Users From Recent Logs */}
      <TopUsersRecent />
    </div>
  );
};

export default DashboardHome;
