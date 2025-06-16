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
                    <span className="usage-value">{usage.totalMemory} GB</span>
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
                                <td>{host.memory} GB</td>
                                <td>{host.gpus}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default UserCurrentUsage; 