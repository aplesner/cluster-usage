import React, { useState } from 'react';
import './UserJobHistory.css';

const UserJobHistory = ({ jobs }) => {
    const [filter, setFilter] = useState('all');
    const [sortBy, setSortBy] = useState('time');
    const [sortOrder, setSortOrder] = useState('desc');

    if (!jobs || jobs.length === 0) {
        return <div className="no-data">No job history available</div>;
    }

    const filteredJobs = jobs.filter(job => {
        if (filter === 'all') return true;
        return job.state.toLowerCase() === filter;
    });

    const sortedJobs = [...filteredJobs].sort((a, b) => {
        const multiplier = sortOrder === 'desc' ? -1 : 1;
        switch (sortBy) {
            case 'time':
                return multiplier * (new Date(b.startTime) - new Date(a.startTime));
            case 'duration':
                return multiplier * (parseRuntime(b.runtime) - parseRuntime(a.runtime));
            case 'resources':
                return multiplier * ((b.cpus + b.gpus) - (a.cpus + a.gpus));
            default:
                return 0;
        }
    });

    const handleSort = (newSortBy) => {
        if (sortBy === newSortBy) {
            setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
        } else {
            setSortBy(newSortBy);
            setSortOrder('desc');
        }
    };

    return (
        <div className="user-job-history">
            <div className="job-history-controls">
                <div className="filter-controls">
                    <button 
                        className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                        onClick={() => setFilter('all')}
                    >
                        All
                    </button>
                    <button 
                        className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
                        onClick={() => setFilter('completed')}
                    >
                        Completed
                    </button>
                    <button 
                        className={`filter-btn ${filter === 'failed' ? 'active' : ''}`}
                        onClick={() => setFilter('failed')}
                    >
                        Failed
                    </button>
                    <button 
                        className={`filter-btn ${filter === 'cancelled' ? 'active' : ''}`}
                        onClick={() => setFilter('cancelled')}
                    >
                        Cancelled
                    </button>
                </div>
            </div>

            <div className="jobs-table-container">
                <table className="jobs-table">
                    <thead>
                        <tr>
                            <th onClick={() => handleSort('time')} className="sortable">
                                Start Time {sortBy === 'time' && (sortOrder === 'desc' ? '\u2193' : '\u2191')}
                            </th>
                            <th>End Time</th>
                            <th>Job ID</th>
                            <th>Host</th>
                            <th>Resources</th>
                            <th onClick={() => handleSort('duration')} className="sortable">
                                Duration {sortBy === 'duration' && (sortOrder === 'desc' ? '\u2193' : '\u2191')}
                            </th>
                            <th>State</th>
                            <th>Command</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedJobs.map((job) => (
                            <tr key={job.jobId} className={`job-status-${job.state.toLowerCase()}`}>
                                <td>{formatDate(job.startTime)}</td>
                                <td>{formatDate(job.endTime)}</td>
                                <td>{job.jobId}</td>
                                <td>{job.host}</td>
                                <td>
                                    <div className="job-resources">
                                        <span className="resource-item">
                                            <span className="resource-label">CPU:</span>
                                            <span className="resource-value">{job.cpus}</span>
                                        </span>
                                        <span className="resource-item">
                                            <span className="resource-label">Mem:</span>
                                            <span className="resource-value">{formatMemory(job.memory)}</span>
                                        </span>
                                        <span className="resource-item">
                                            <span className="resource-label">GPU:</span>
                                            <span className="resource-value">{job.gpus}</span>
                                        </span>
                                    </div>
                                </td>
                                <td>{formatRuntime(job.runtime)}</td>
                                <td>
                                    <span className={`job-state job-state-${job.state.toLowerCase()}`}>
                                        {job.state}
                                    </span>
                                </td>
                                <td className="job-command" title={job.command}>
                                    {truncateCommand(job.command)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
};

const formatMemory = (bytes) => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let value = bytes;
    let unitIndex = 0;

    while (value >= 1024 && unitIndex < units.length - 1) {
        value /= 1024;
        unitIndex++;
    }

    return `${value.toFixed(1)} ${units[unitIndex]}`;
};

const formatRuntime = (runtime) => {
    if (!runtime) return '';
    // Support D-HH:MM:SS, HH:MM:SS, MM:SS
    let days = 0, hours = 0, minutes = 0, seconds = 0;
    const dMatch = runtime.match(/^(\d+)-(\d+):(\d+):(\d+)$/);
    if (dMatch) {
        days = Number(dMatch[1]);
        hours = Number(dMatch[2]);
        minutes = Number(dMatch[3]);
        seconds = Number(dMatch[4]);
    } else {
        const hMatch = runtime.match(/^(\d+):(\d+):(\d+)$/);
        if (hMatch) {
            hours = Number(hMatch[1]);
            minutes = Number(hMatch[2]);
            seconds = Number(hMatch[3]);
        } else {
            const mMatch = runtime.match(/^(\d+):(\d+)$/);
            if (mMatch) {
                minutes = Number(mMatch[1]);
                seconds = Number(mMatch[2]);
            }
        }
    }
    let result = '';
    if (days > 0) result += `${days}d `;
    if (hours > 0) result += `${hours}h `;
    if (minutes > 0) result += `${minutes}m `;
    if (seconds > 0 && days === 0) result += `${seconds}s`;
    return result.trim();
};

const parseRuntime = (runtime) => {
    const [hours, minutes, seconds] = runtime.split(':').map(Number);
    return hours * 3600 + minutes * 60 + seconds;
};

const truncateCommand = (command) => {
    const maxLength = 50;
    if (command.length <= maxLength) return command;
    return command.substring(0, maxLength) + '...';
};

export default UserJobHistory; 