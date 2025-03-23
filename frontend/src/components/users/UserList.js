import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

const UserList = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'session_count', direction: 'desc' });

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const data = await api.getUsers();
        setUsers(data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching users:', error);
        setError(error.message || 'Failed to fetch users');
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  // Filter users based on search term and role filter
  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.user_affiliation && user.user_affiliation.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesRole = 
      roleFilter === '' || 
      (user.user_role && user.user_role.toLowerCase() === roleFilter.toLowerCase());
    
    return matchesSearch && matchesRole;
  });

  // Sort users based on sortConfig
  const sortedUsers = [...filteredUsers].sort((a, b) => {
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

  // Get available roles for filtering
  const availableRoles = [...new Set(users.filter(user => user.user_role).map(user => user.user_role))];

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="users-container">
      <h2 className="page-title">User Statistics</h2>
      
      <div className="search-filter">
        <input
          type="text"
          className="search-input"
          placeholder="Search by username or affiliation..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        
        <select 
          className="filter-select"
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
        >
          <option value="">All Roles</option>
          {availableRoles.map(role => (
            <option key={role} value={role}>{role}</option>
          ))}
        </select>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>All Users ({sortedUsers.length})</h3>
        </div>
        <div className="card-body">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th 
                    className={getSortClass('username')}
                    onClick={() => requestSort('username')}
                  >
                    Username
                  </th>
                  <th>Role</th>
                  <th>Affiliation</th>
                  <th 
                    className={getSortClass('session_count')}
                    onClick={() => requestSort('session_count')}
                  >
                    Sessions
                  </th>
                  <th 
                    className={getSortClass('machine_count')}
                    onClick={() => requestSort('machine_count')}
                  >
                    Machines
                  </th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedUsers.length > 0 ? (
                  sortedUsers.map(user => (
                    <tr key={user.user_id}>
                      <td>{user.username}</td>
                      <td>
                        {user.user_role && (
                          <span className={getRoleBadgeClass(user.user_role)}>
                            {user.user_role}
                          </span>
                        )}
                      </td>
                      <td>{user.user_affiliation || '-'}</td>
                      <td>{user.session_count}</td>
                      <td>{user.machine_count}</td>
                      <td>
                        <Link to={`/users/${user.username}`} className="btn">
                          View Profile
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center' }}>
                      No users found matching your filters
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

export default UserList;

