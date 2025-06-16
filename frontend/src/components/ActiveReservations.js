import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import LoadingSpinner from './common/LoadingSpinner';
import ErrorMessage from './common/ErrorMessage';
import './ActiveReservations.css';

function ActiveReservations() {
    const [reservations, setReservations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchReservations = async () => {
        try {
            const data = await api.getActiveCalendarEvents();
            setReservations(data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching active reservations:', error);
            setError(error.message || 'Failed to fetch active reservations');
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReservations();
        const interval = setInterval(fetchReservations, 60000); // Refresh every minute
        return () => clearInterval(interval);
    }, []);

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

    if (loading) return <LoadingSpinner />;
    if (error) return <ErrorMessage message={error} />;

    return (
        <div className="active-reservations">
            <div className="format-guide">
                <h3>Calendar Event Format Guide</h3>
                <p>Events should be formatted as follows:</p>
                <ul>
                    <li>For specific resources: <code>username @ NRx resource1, NRx resource2 (comment)</code></li>
                    <li>Example: <code>wattenhofer @ 8x tikgpu10 (ICML deadline)</code></li>
                    <li>For estimated resources: <code>username @ NRx tikgpuX</code></li>
                    <li>Example: <code>wattenhofer @ 12x tikgpuX</code></li>
                </ul>
            </div>

            <h2>Active Reservations</h2>
            {reservations.length === 0 ? (
                <p>No active reservations at the moment.</p>
            ) : (
                <div className="reservations-list">
                    {reservations.map((reservation, index) => (
                        <div key={index} className="reservation-card">
                            <div className="user-header">
                                <div className="user-info">
                                    <span className="username">{reservation.username}</span>
                                    {reservation.user_role && (
                                        <span className={getRoleBadgeClass(reservation.user_role)}>
                                            {reservation.user_role}
                                        </span>
                                    )}
                                </div>
                                <Link to={`/users/${reservation.username}`} className="btn btn-sm">
                                    Visit User
                                </Link>
                            </div>
                            <div className="duration">{reservation.duration}</div>
                            <div className="resources-tags">
                                {reservation.resources.map(([num, resource], idx) => (
                                    <span key={idx} className="resource-tag">
                                        {num}x {resource}
                                    </span>
                                ))}
                            </div>
                            {reservation.comment && (
                                <div className="comment">{reservation.comment}</div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default ActiveReservations; 