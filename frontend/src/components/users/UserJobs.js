import React from 'react';
import './UserJobs.css';

const UserJobs = ({ jobs, isRunningJobs = false }) => {
    if (!jobs || jobs.length === 0) {
        return <div className="no-data">No {isRunningJobs ? 'running' : 'historical'} jobs</div>;
    }

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
                            {!isRunningJobs && <th>End Time</th>}
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
                                {!isRunningJobs && <td>{job.endTime ? new Date(job.endTime).toLocaleString() : ''}</td>}
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