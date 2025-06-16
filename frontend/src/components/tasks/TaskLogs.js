import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

const TaskLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'timestamp', direction: 'desc' });
  const [taskFilter, setTaskFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data = await api.getTaskLogs();
        setLogs(data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching task logs:', error);
        setError(error.message || 'Failed to fetch task logs');
        setLoading(false);
      }
    };

    fetchLogs();
  }, []);

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Filter logs based on task name and status
  const filteredLogs = logs.filter(log => {
    const matchesTask = !taskFilter || log.task_name.toLowerCase().includes(taskFilter.toLowerCase());
    const matchesStatus = !statusFilter || log.status.toLowerCase() === statusFilter.toLowerCase();
    return matchesTask && matchesStatus;
  });

  // Sort logs based on sortConfig
  const sortedLogs = [...filteredLogs].sort((a, b) => {
    if (sortConfig.key === 'timestamp') {
      const dateA = new Date(a[sortConfig.key]);
      const dateB = new Date(b[sortConfig.key]);
      return sortConfig.direction === 'asc' ? dateA - dateB : dateB - dateA;
    }
    
    if (a[sortConfig.key] < b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (a[sortConfig.key] > b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

  // Request a sort
  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Get class name for the sort header
  const getSortClass = (key) => {
    if (sortConfig.key !== key) return 'sort-header';
    return sortConfig.direction === 'asc' 
      ? 'sort-header sort-asc' 
      : 'sort-header sort-desc';
  };

  // Get status badge class
  const getStatusBadgeClass = (status) => {
    const statusLower = status.toLowerCase();
    if (statusLower === 'success') return 'badge badge-success';
    if (statusLower === 'error') return 'badge badge-error';
    return 'badge';
  };

  // Get available tasks and statuses for filtering
  const availableTasks = [...new Set(logs.map(log => log.task_name))];
  const availableStatuses = [...new Set(logs.map(log => log.status))];

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="tasks-container">
      <h2 className="page-title">Periodic Task Logs</h2>
      
      <div className="search-filter">
        <input
          type="text"
          className="search-input"
          placeholder="Filter by task name..."
          value={taskFilter}
          onChange={(e) => setTaskFilter(e.target.value)}
        />
        
        <select 
          className="filter-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          {availableStatuses.map(status => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Task Execution Logs ({sortedLogs.length})</h3>
        </div>
        <div className="card-body">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th 
                    className={getSortClass('timestamp')}
                    onClick={() => requestSort('timestamp')}
                  >
                    Timestamp
                  </th>
                  <th 
                    className={getSortClass('task_name')}
                    onClick={() => requestSort('task_name')}
                  >
                    Task Name
                  </th>
                  <th 
                    className={getSortClass('status')}
                    onClick={() => requestSort('status')}
                  >
                    Status
                  </th>
                  <th>Message</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {sortedLogs.length > 0 ? (
                  sortedLogs.map(log => (
                    <tr key={log.log_id}>
                      <td>{formatDate(log.timestamp)}</td>
                      <td>{log.task_name}</td>
                      <td>
                        <span className={getStatusBadgeClass(log.status)}>
                          {log.status}
                        </span>
                      </td>
                      <td>{log.message || '-'}</td>
                      <td>
                        {log.details ? (
                          <pre className="log-details">{log.details}</pre>
                        ) : '-'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center' }}>
                      No task logs found matching your filters
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskLogs; 