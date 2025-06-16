import React from 'react';
import ActiveReservations from '../ActiveReservations';
import CurrentUsage from './CurrentUsage';

const CalendarView = () => {
  return (
    <div className="calendar-container">
      <h2 className="page-title">Cluster Calendar</h2>
      
      {/* Active Reservations Section */}
      <ActiveReservations />
      
      {/* Calendar Section */}
      <div className="card">
        <div className="card-header">
          <h3>Cluster Usage Calendar</h3>
        </div>
        <div className="card-body">
          <div className="calendar-frame-container">
            <iframe
              src="https://calendar.google.com/calendar/embed?src=97b9d921cbee75fb048013a177956dff66bef6eafc0cbedcf14b58acad7e414e%40group.calendar.google.com"
              style={{ border: 0, width: '100%', height: '600px' }}
              frameBorder="0"
              scrolling="no"
              title="Cluster Usage Calendar"
            />
          </div>
        </div>
      </div>

      {/* Current Usage Section */}
      <CurrentUsage />
    </div>
  );
};

export default CalendarView; 