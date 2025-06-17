import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

const TaskLogs = () => {
  const [logs, setLogs] = useState([]);
  const [emailNotifications, setEmailNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'timestamp', direction: 'desc' });
  const [taskFilter, setTaskFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [emailSortConfig, setEmailSortConfig] = useState({ key: 'timestamp', direction: 'desc' });
  
  // Pagination state
  const [emailPagination, setEmailPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0
  });
  const [taskPagination, setTaskPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0
  });

  const fetchData = async (emailPage = 1, taskPage = 1) => {
    try {
      setLoading(true);
      const [emailData, taskData] = await Promise.all([
        api.getEmailNotifications(emailPage, 20),
        api.getTaskLogs(taskPage, 20)
      ]);
      
      setEmailNotifications(emailData.notifications || []);
      setEmailPagination(emailData.pagination || { page: 1, limit: 20, total: 0, pages: 0 });
      
      setLogs(taskData.logs || []);
      setTaskPagination(taskData.pagination || { page: 1, limit: 20, total: 0, pages: 0 });
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError(error.message || 'Failed to fetch data');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
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

  // Request a sort for email notifications
  const requestEmailSort = (key) => {
    let direction = 'asc';
    if (emailSortConfig.key === key && emailSortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setEmailSortConfig({ key, direction });
  };

  // Get class name for the sort header
  const getSortClass = (key) => {
    if (sortConfig.key !== key) return 'sort-header';
    return sortConfig.direction === 'asc' 
      ? 'sort-header sort-asc' 
      : 'sort-header sort-desc';
  };

  // Get class name for the email sort header
  const getEmailSortClass = (key) => {
    if (emailSortConfig.key !== key) return 'sort-header';
    return emailSortConfig.direction === 'asc' 
      ? 'sort-header sort-asc' 
      : 'sort-header sort-desc';
  };

  // Sort email notifications
  const sortedEmailNotifications = [...emailNotifications].sort((a, b) => {
    if (emailSortConfig.key === 'timestamp') {
      const dateA = new Date(a[emailSortConfig.key]);
      const dateB = new Date(b[emailSortConfig.key]);
      return emailSortConfig.direction === 'asc' ? dateA - dateB : dateB - dateA;
    }
    
    if (a[emailSortConfig.key] < b[emailSortConfig.key]) {
      return emailSortConfig.direction === 'asc' ? -1 : 1;
    }
    if (a[emailSortConfig.key] > b[emailSortConfig.key]) {
      return emailSortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

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

  // Pagination handlers
  const handleEmailPageChange = (newPage) => {
    fetchData(newPage, taskPagination.page);
  };

  const handleTaskPageChange = (newPage) => {
    fetchData(emailPagination.page, newPage);
  };

  // Pagination component
  const Pagination = ({ currentPage, totalPages, onPageChange, totalItems }) => {
    if (totalPages <= 1) return null;
    
    const pages = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return (
      <div className="pagination">
        <div className="pagination-info">
          Showing {((currentPage - 1) * 20) + 1} to {Math.min(currentPage * 20, totalItems)} of {totalItems} items
        </div>
        <div className="pagination-controls">
          <button 
            className="pagination-btn"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          
          {startPage > 1 && (
            <>
              <button 
                className="pagination-btn"
                onClick={() => onPageChange(1)}
              >
                1
              </button>
              {startPage > 2 && <span className="pagination-ellipsis">...</span>}
            </>
          )}
          
          {pages.map(page => (
            <button
              key={page}
              className={`pagination-btn ${page === currentPage ? 'active' : ''}`}
              onClick={() => onPageChange(page)}
            >
              {page}
            </button>
          ))}
          
          {endPage < totalPages && (
            <>
              {endPage < totalPages - 1 && <span className="pagination-ellipsis">...</span>}
              <button 
                className="pagination-btn"
                onClick={() => onPageChange(totalPages)}
              >
                {totalPages}
              </button>
            </>
          )}
          
          <button 
            className="pagination-btn"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="tasks-container">
      <h2 className="page-title">Task Logs & Email Notifications</h2>
      
      {/* Email Notifications Section */}
      <div className="card">
        <div className="card-header">
          <h3>Email Notifications ({emailPagination.total} total)</h3>
        </div>
        <div className="card-body">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th 
                    className={getEmailSortClass('timestamp')}
                    onClick={() => requestEmailSort('timestamp')}
                  >
                    Timestamp
                  </th>
                  <th 
                    className={getEmailSortClass('email_type')}
                    onClick={() => requestEmailSort('email_type')}
                  >
                    Type
                  </th>
                  <th 
                    className={getEmailSortClass('status')}
                    onClick={() => requestEmailSort('status')}
                  >
                    Status
                  </th>
                  <th>Message</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {sortedEmailNotifications.length > 0 ? (
                  sortedEmailNotifications.map((notification, index) => (
                    <tr key={index}>
                      <td>{formatDate(notification.timestamp)}</td>
                      <td>
                        <span className="badge badge-info">
                          {notification.email_type}
                        </span>
                      </td>
                      <td>
                        <span className={getStatusBadgeClass(notification.status)}>
                          {notification.status}
                        </span>
                      </td>
                      <td>{notification.message || '-'}</td>
                      <td>
                        {notification.details ? (
                          <pre className="log-details">{notification.details}</pre>
                        ) : '-'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center' }}>
                      No email notifications found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <Pagination
        currentPage={emailPagination.page}
        totalPages={emailPagination.pages}
        onPageChange={handleEmailPageChange}
        totalItems={emailPagination.total}
      />
      
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
          <h3>Periodic Task Logs ({taskPagination.total} total)</h3>
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
      
      <Pagination
        currentPage={taskPagination.page}
        totalPages={taskPagination.pages}
        onPageChange={handleTaskPageChange}
        totalItems={taskPagination.total}
      />
    </div>
  );
};

export default TaskLogs; 