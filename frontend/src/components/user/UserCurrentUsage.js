import React from 'react';
import './UserCurrentUsage.css';

const UserCurrentUsage = ({ usage }) => {
    if (!usage) return <div className="no-data">No current usage data available</div>;

    return (
        <div className="user-current-usage">
            <div className="usage-summary">
                <div className="usage-item">
                    <span className="usage-label">Total CPUs:</span>
                    <span className="usage-value">{usage.totalCpus}</span>
                </div>
                <div className="usage-item">
                    <span className="usage-label">Total Memory:</span>
                    <span className="usage-value">{formatMemory(usage.totalMemory)}</span>
                </div>
                <div className="usage-item">
                    <span className="usage-label">Total GPUs:</span>
                    <span className="usage-value">{usage.totalGpus}</span>
                </div>
            </div>

            <div className="usage-details">
                <table className="usage-table">
                    <thead>
                        <tr>
                            <th>Host</th>
                            <th>CPUs</th>
                            <th>Memory</th>
                            <th>GPUs</th>
                        </tr>
                    </thead>
                    <tbody>
                        {usage.hosts.map((host, index) => (
                            <tr key={index}>
                                <td>{host.name}</td>
                                <td>{host.cpus}</td>
                                <td>{formatMemory(host.memory)}</td>
                                <td>{host.gpus}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
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

export default UserCurrentUsage; 