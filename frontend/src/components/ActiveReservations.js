import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import LoadingSpinner from './common/LoadingSpinner';
import ErrorMessage from './common/ErrorMessage';
import './ActiveReservations.css';

function ActiveReservations() {
    const [reservations, setReservations] = useState([]);
    const [unparsed, setUnparsed] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastRefresh, setLastRefresh] = useState(null);

    const fetchReservations = async () => {
        try {
            const data = await api.getActiveCalendarEvents();
            if (Array.isArray(data)) {
                setReservations(data);
                setUnparsed([]);
            } else {
                setReservations(data.active_events || []);
                setUnparsed(data.unparsed_events || []);
            }
            setLoading(false);
        } catch (error) {
            console.error('Error fetching active reservations:', error);
            setError(error.message || 'Failed to fetch active reservations');
            setLoading(false);
        }
    };

    const fetchLastRefresh = async () => {
        try {
            const data = await api.getCalendarLastRefresh();
            setLastRefresh(data.last_refresh);
        } catch (error) {
            setLastRefresh(null);
        }
    };

    useEffect(() => {
        fetchReservations();
        fetchLastRefresh();
        const interval = setInterval(() => {
            fetchReservations();
            fetchLastRefresh();
        }, 60000); // Refresh every minute
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

    // Helper to check if a reservation is tikgpuX only
    const isTikgpuXReservation = (reservation) => {
        if (!reservation.resources || reservation.resources.length === 0) return false;
        // True if all resources are tikgpuX (case-insensitive)
        return reservation.resources.every(([_, resource]) =>
            typeof resource === 'string' && resource.trim().toLowerCase() === 'tikgpux'
        );
    };
    // Split reservations
    const tikgpuXReservations = reservations.filter(isTikgpuXReservation);
    const nonTikgpuXReservations = reservations.filter(r => !isTikgpuXReservation(r));

    // Helper to format how long ago the last refresh was
    const getTimeAgo = (isoString) => {
        if (!isoString) return 'N/A';
        const now = new Date();
        const last = new Date(isoString);
        
        // Ensure both dates are in the same timezone context for accurate comparison
        // The backend sends timezone-aware ISO strings in CET/CEST
        const diffMs = now.getTime() - last.getTime();
        if (diffMs < 0) return 'just now';
        
        const minutes = Math.floor(diffMs / 60000);
        const seconds = Math.floor((diffMs % 60000) / 1000);
        return `${minutes}m ${seconds}s ago`;
    };

    if (loading) return <LoadingSpinner />;
    if (error) return <ErrorMessage message={error} />;

    return (
        <div className="active-reservations">

            <h2 style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                Active Reservations
                <span style={{ fontSize: '1rem', color: '#888', fontWeight: 'normal' }}>
                    (refreshed {getTimeAgo(lastRefresh)})
                </span>
            </h2>

            {/* Red Box: Do not use these reserved resources */}
            {nonTikgpuXReservations.length > 0 ? (
                <div className="rule-box" style={{ marginTop: '1rem' }}>
                    <div style={{ marginBottom: '0.5rem' }}>
                        These resources are reserved for the users below. Please do not use them during the reservation period.
                    </div>
                    <div className="reservations-list">
                        {nonTikgpuXReservations.map((reservation, index) => (
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
                </div>
            ) : (
                <div className="empty-box" style={{ marginTop: '1rem' }}>
                    No active reservations.
                </div>
            )}

            <h2>Announcements</h2>
            {/* Blue Box: Announcements */}
            {tikgpuXReservations.length > 0 ? (
                <div className="info-box" style={{ marginTop: '1rem' }}>
                    <div style={{ marginBottom: '0.5rem' }}>
                        These users are allowed to use more than the 4 GPUs, but you do not need to check that the resources are available (they are not reserved)
                    </div>
                    <div className="reservations-list" style={{ marginTop: '1rem' }}>
                        {tikgpuXReservations.map((reservation, index) => (
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
                </div>
            ) : (
                <div className="empty-box" style={{ marginTop: '1rem' }}>
                    No active announcements.
                </div>
            )}

            {unparsed.length > 0 && (
                <div className="unparsed-reservations">
                    <h3>Unparsed Reservations</h3>
                    <ul>
                        {unparsed.map((summary, idx) => (
                            <li key={idx}><code>{summary}</code></li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export default ActiveReservations; 