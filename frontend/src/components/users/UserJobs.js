import React from 'react';
import './UserJobs.css';

const UserJobs = ({ jobs, isRunningJobs = false }) => {
    if (!jobs || jobs.length === 0) {
        return <div className="no-data">No {isRunningJobs ? 'running' : 'historical'} jobs</div>;
    }

    const formatRuntime = (runtime) => {
        // Convert runtime string (HH:MM:SS) to a more readable format
        const [hours, minutes, seconds] = runtime.split(':').map(Number);
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds}s`;
        } else {
            return `${seconds}s`;
        }
    };

    const truncateCommand = (command) => {
        const maxLength = 50;
        if (command.length <= maxLength) return command;
        return command.substring(0, maxLength) + '...';
    };

    return (
        <div className="user-jobs">
            <div className="jobs-table-container">
                <table className="jobs-table">
                    <thead>
                        <tr>
                            <th>Job ID</th>
                            <th>Host</th>
                            <th>Resources</th>
                            <th>Runtime</th>
                            {!isRunningJobs && <th>Status</th>}
                            <th>Command</th>
                        </tr>
                    </thead>
                    <tbody>
                        {jobs.map((job) => (
                            <tr key={job.jobId} className={`job-status-${job.state.toLowerCase()}`}>
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
                                            <span className="resource-value">{job.memory} GB</span>
                                        </span>
                                        {job.gpus > 0 && (
                                            <span className="resource-item">
                                                <span className="resource-label">GPU:</span>
                                                <span className="resource-value">{job.gpus}</span>
                                            </span>
                                        )}
                                    </div>
                                </td>
                                <td>{formatRuntime(job.runtime)}</td>
                                {!isRunningJobs && (
                                    <td>
                                        <span className={`status-badge status-${job.state.toLowerCase()}`}>
                                            {job.state}
                                        </span>
                                    </td>
                                )}
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

export default UserJobs; 