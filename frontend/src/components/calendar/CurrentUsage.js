import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import './CurrentUsage.css';

const CurrentUsage = () => {
    const [usageData, setUsageData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortConfig, setSortConfig] = useState({ key: 'total_gpus', direction: 'desc' });
    const [gpuHours, setGpuHours] = useState({});
    const [gpuHoursLoading, setGpuHoursLoading] = useState(false);
    const [emailedUsers, setEmailedUsers] = useState([]);
    const [thesesSupervisors, setThesesSupervisors] = useState([]);
    const [thesesLoading, setThesesLoading] = useState(true);
    const [thesesError, setThesesError] = useState(null);

    const fetchUsageData = async () => {
        try {
            const data = await api.getCurrentUsage();
            setUsageData(data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching current usage:', error);
            setError(error.message || 'Failed to fetch current usage data');
            setLoading(false);
        }
    };

    // Fetch GPU hours for all users in the table
    const fetchAllGpuHours = async (users) => {
        setGpuHoursLoading(true);
        try {
            const allGpuHours = await api.getAllUsersGpuHours();
            const hoursMap = {};
            users.forEach(user => {
                hoursMap[user.user] = allGpuHours[user.user] !== undefined ? allGpuHours[user.user] : null;
            });
            setGpuHours(hoursMap);
        } catch {
            // fallback: set all to null
            const hoursMap = {};
            users.forEach(user => { hoursMap[user.user] = null; });
            setGpuHours(hoursMap);
        }
        setGpuHoursLoading(false);
    };

    // Fetch users emailed in last 12 hours
    const fetchEmailedUsers = async () => {
        try {
            const data = await api.getUsersEmailedLast12h();
            setEmailedUsers(data.emailed_users || []);
        } catch {
            setEmailedUsers([]);
        }
    };

    useEffect(() => {
        fetchUsageData();
        fetchEmailedUsers();
        // Fetch all theses and supervisors
        const fetchTheses = async () => {
            try {
                setThesesLoading(true);
                const data = await api.getAllThesesSupervisors();
                setThesesSupervisors(data);
                setThesesError(null);
            } catch (err) {
                setThesesSupervisors([]);
                setThesesError('Failed to fetch theses and supervisors');
            } finally {
                setThesesLoading(false);
            }
        };
        fetchTheses();
        const interval = setInterval(() => {
            fetchUsageData();
            fetchEmailedUsers();
            fetchTheses();
        }, 60000); // Refresh every minute
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (usageData?.usage) {
            fetchAllGpuHours(usageData.usage);
        }
    }, [usageData]);

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

    // Get host tag class based on host name
    const getHostTagClass = (host) => {
        if (host.startsWith('tikgpu02') || host.startsWith('tikgpu03') || host.startsWith('tikgpu04')) {
            return 'host-tag host-tag-green';
        } else if (host.startsWith('tikgpu05') || host.startsWith('tikgpu06') || 
                  host.startsWith('tikgpu07') || host.startsWith('tikgpu09')) {
            return 'host-tag host-tag-blue';
        } else if (host.startsWith('tikgpu08') || host.startsWith('tikgpu10')) {
            return 'host-tag host-tag-red';
        }
        return 'host-tag';
    };

    // Sort the data
    const sortedData = usageData?.usage ? [...usageData.usage].sort((a, b) => {
        if (sortConfig.direction === 'asc') {
            return a[sortConfig.key] - b[sortConfig.key];
        }
        return b[sortConfig.key] - a[sortConfig.key];
    }) : [];

    if (loading) return <LoadingSpinner />;
    if (error) return <ErrorMessage message={error} />;

    return (
        <div className="current-usage">
            <div className="card">
                <div className="card-header">
                    <h3>Current Resource Usage</h3>
                    <div className="last-updated">
                        Last updated: {usageData?.timestamp ?
                            new Date(usageData.timestamp.replace(' ', 'T')).toLocaleString() : 'N/A'}
                    </div>
                    {usageData?.timestamp && (
                        <div style={{ color: '#888', fontSize: '0.95em', marginTop: '0.2em' }}>
                            {(() => {
                                const now = new Date();
                                const last = new Date(usageData.timestamp.replace(' ', 'T'));
                                const diffMs = now - last;
                                const hours = diffMs / 3600000;
                                return `(${hours.toFixed(1)} hours ago)`;
                            })()}
                        </div>
                    )}
                </div>
                <div className="card-body">
                    <div className="table-container">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>User</th>
                                    <th title="System Flags">🏳️</th>
                                    <th>Role</th>
                                    <th 
                                        className={getSortClass('total_cpus')}
                                        onClick={() => requestSort('total_cpus')}
                                    >
                                        CPUs
                                    </th>
                                    <th 
                                        className={getSortClass('total_memory_gb')}
                                        onClick={() => requestSort('total_memory_gb')}
                                    >
                                        Memory (GB)
                                    </th>
                                    <th 
                                        className={getSortClass('total_gpus')}
                                        onClick={() => requestSort('total_gpus')}
                                    >
                                        GPUs
                                    </th>
                                    <th>Total GPU Hours</th>
                                    <th>Hosts</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sortedData.length > 0 ? (
                                    sortedData.map((user) => (
                                        <tr key={user.user}>
                                            <td>{user.user}</td>
                                            <td style={{ textAlign: 'center', fontSize: '1.3em' }}>
                                                {emailedUsers.includes(user.user) ? <span title="User received an email in the last 12h">📧</span> : ''}
                                            </td>
                                            <td>
                                                {user.user_role && (
                                                    <span className={getRoleBadgeClass(user.user_role)}>
                                                        {user.user_role}
                                                    </span>
                                                )}
                                            </td>
                                            <td>{user.total_cpus}</td>
                                            <td>{user.total_memory_gb.toFixed(1)}</td>
                                            <td>{user.total_gpus}</td>
                                            <td>{gpuHoursLoading ? <span>...</span> : (gpuHours[user.user] !== null && gpuHours[user.user] !== undefined ? gpuHours[user.user].toFixed(2) : 'N/A')}</td>
                                            <td>
                                                <div className="hosts-list">
                                                    {user.hosts.map((host, idx) => (
                                                        <span key={idx} className={getHostTagClass(host.name)}>
                                                            {host.gpus > 0 ? `${host.gpus}x ` : ''}{host.name}
                                                        </span>
                                                    ))}
                                                </div>
                                            </td>
                                            <td>
                                                <Link to={`/users/${user.user}`} className="btn btn-sm">
                                                    View Details
                                                </Link>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="9" style={{ textAlign: 'center' }}>
                                            No active jobs found
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            {/* Theses and Supervisors Table */}
            <div className="card" style={{ marginTop: 32 }}>
                <div className="card-header">
                    <h3>Theses and Supervisors (from database)</h3>
                </div>
                <div className="card-body">
                    {thesesLoading ? (
                        <LoadingSpinner />
                    ) : thesesError ? (
                        <ErrorMessage message={thesesError} />
                    ) : (
                        <div className="table-container">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Student Username</th>
                                        <th>Thesis Title</th>
                                        <th>Semester</th>
                                        <th>Supervisors</th>
                                        <th>View Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {thesesSupervisors.length > 0 ? (
                                        thesesSupervisors.map((entry, idx) => (
                                            <tr key={idx}>
                                                <td>{entry.student_username}</td>
                                                <td>{entry.thesis_title}</td>
                                                <td>{entry.semester}</td>
                                                <td>{entry.supervisors && entry.supervisors.length > 0 ? entry.supervisors.join(', ') : '-'}</td>
                                                <td>
                                                    <Link to={`/users/${entry.student_username}`} className="btn btn-sm">
                                                        View Details
                                                    </Link>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="5" style={{ textAlign: 'center' }}>
                                                No thesis-supervisor data found
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CurrentUsage; 