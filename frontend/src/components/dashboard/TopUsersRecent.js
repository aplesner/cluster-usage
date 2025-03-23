import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

const TopUsersRecent = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getTopUsersRecent();
        setData(response);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching top users:', error);
        setError(error.message || 'Failed to fetch top users data');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Format date range
  const formatDateRange = (dateRange) => {
    if (!dateRange || !dateRange.min_date || !dateRange.max_date) {
      return 'Recent logs';
    }
    
    const minDate = new Date(dateRange.min_date);
    const maxDate = new Date(dateRange.max_date);
    
    const formatDate = (date) => {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    return `${formatDate(minDate)} - ${formatDate(maxDate)}`;
  };

  // Get badge class based on user role
  const getRoleBadgeClass = (role) => {
    if (!role) return 'badge';
    
    const roleLower = role.toLowerCase();
    if (roleLower === 'staff') return 'badge badge-staff';
    if (roleLower === 'guest') return 'badge badge-guest';
    if (roleLower === 'stud') return 'badge badge-stud';
    if (roleLower === 'ueb') return 'badge badge-ueb';
    
    return 'badge';
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!data || !data.users || data.users.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3>Most Active Users (Recent Logs)</h3>
        </div>
        <div className="card-body">
          <p>No recent activity data available.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>Most Active Users ({formatDateRange(data.date_range)})</h3>
      </div>
      <div className="card-body">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Role</th>
                <th>Operations</th>
                <th>Sessions</th>
                <th>Machines</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.users.map((user, index) => (
                <tr key={index}>
                  <td>{user.username}</td>
                  <td>
                    {user.user_role && (
                      <span className={getRoleBadgeClass(user.user_role)}>
                        {user.user_role}
                      </span>
                    )}
                  </td>
                  <td>{user.total_operations.toLocaleString()}</td>
                  <td>{user.session_count}</td>
                  <td title={user.machines}>{user.machine_count}</td>
                  <td>
                    <Link to={`/users/${user.username}`} className="btn">
                      View Profile
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TopUsersRecent;

