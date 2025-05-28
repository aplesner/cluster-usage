import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

const HistoricUsage = () => {
  const [historicData, setHistoricData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [topN, setTopN] = useState(10);
  const [expandedLogs, setExpandedLogs] = useState({});

  // Use useCallback to memoize the function and fix the dependency warning
  const fetchHistoricData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getHistoricUsage(topN);
      setHistoricData(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching historic data:', error);
      setError(error.message || 'Failed to fetch historic usage data');
      setLoading(false);
    }
  }, [topN]); // Include topN as dependency since it's used in the function

  useEffect(() => {
    fetchHistoricData();
  }, [fetchHistoricData]); // Now fetchHistoricData is properly memoized
  
  // Sort historic data by timestamp (most recent first)
  const sortedHistoricData = [...historicData].sort((a, b) => {
    return new Date(b.timestamp) - new Date(a.timestamp);
  });

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Toggle expanded state for a log entry
  const toggleExpand = (logId) => {
    setExpandedLogs(prev => ({
      ...prev,
      [logId]: !prev[logId]
    }));
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

  return (
    <div className="historic-usage-container">
      <div className="page-header">
        <h2 className="page-title">Historic Usage</h2>
        <div className="top-n-selector">
          <label htmlFor="top-n">Top users per log entry: </label>
          <select 
            id="top-n" 
            value={topN} 
            onChange={(e) => setTopN(parseInt(e.target.value))}
            className="filter-select"
          >
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="15">15</option>
            <option value="20">20</option>
            <option value="25">25</option>
          </select>
        </div>
      </div>
      
      {historicData.length === 0 ? (
        <div className="card">
          <div className="card-body">
            <p>No historic data available.</p>
          </div>
        </div>
      ) : (
        <div className="log-entries-list">
          {sortedHistoricData.map((logEntry) => (
            <div key={logEntry.log_id} className="card log-entry-card">
              <div 
                className="card-header log-entry-header" 
                onClick={() => toggleExpand(logEntry.log_id)}
              >
                <h3>
                  {formatDate(logEntry.timestamp)}
                  <span className="expand-icon">
                    {expandedLogs[logEntry.log_id] ? '▼' : '►'}
                  </span>
                </h3>
              </div>
              
              {expandedLogs[logEntry.log_id] && (
                <div className="card-body">
                  <div className="table-container">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Rank</th>
                          <th>Username</th>
                          <th>Role</th>
                          <th>Operations</th>
                          <th>Machines</th>
                        </tr>
                      </thead>
                      <tbody>
                        {logEntry.top_users.length > 0 ? (
                          logEntry.top_users.map((user, index) => (
                            <tr key={index}>
                              <td>#{index + 1}</td>
                              <td>{user.username}</td>
                              <td>
                                {user.user_role && (
                                  <span className={getRoleBadgeClass(user.user_role)}>
                                    {user.user_role}
                                  </span>
                                )}
                              </td>
                              <td>{user.total_operations.toLocaleString()}</td>
                              <td title={user.machines}>
                                {user.machine_count} machine{user.machine_count !== 1 ? 's' : ''}
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan="5" className="text-center">
                              No user data available for this log entry
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistoricUsage;