import React, { useState, useEffect } from 'react';
import UserCurrentUsage from './UserCurrentUsage';
import UserRunningJobs from './UserRunningJobs';
import UserJobHistory from './UserJobHistory';
import './UserOverview.css';

const UserOverview = ({ username }) => {
    const [userData, setUserData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchUserData = async () => {
            try {
                setLoading(true);
                const response = await fetch(`/api/users/${username}/overview`);
                if (!response.ok) {
                    throw new Error('Failed to fetch user data');
                }
                const data = await response.json();
                setUserData(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchUserData();
    }, [username]);

    if (loading) return <div className="loading">Loading user data...</div>;
    if (error) return <div className="error">Error: {error}</div>;
    if (!userData) return <div className="error">No data available</div>;

    return (
        <div className="user-overview">
            <h2>User Overview: {username}</h2>
            
            <div className="user-overview-grid">
                <div className="user-overview-section">
                    <h3>Current Resource Usage</h3>
                    <UserCurrentUsage usage={userData.currentUsage} />
                </div>

                <div className="user-overview-section">
                    <h3>Running Jobs</h3>
                    <UserRunningJobs jobs={userData.runningJobs} />
                </div>

                <div className="user-overview-section full-width">
                    <h3>Job History</h3>
                    <UserJobHistory jobs={userData.jobHistory} />
                </div>
            </div>
        </div>
    );
};

export default UserOverview; 