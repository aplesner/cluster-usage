import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchAllTheses, getAllUsers, getCurrentUsageAll } from '../services/api';
import LoadingSpinner from './common/LoadingSpinner';
import ErrorMessage from './common/ErrorMessage';
import ActiveReservations from './ActiveReservations';
import CurrentUsage from './calendar/CurrentUsage';
import CollapsibleSection from './CollapsibleSection';
// import Announcements from './Announcements'; // Uncomment if Announcements component exists
import './PhdThesisPage.css';
import api from '../services/api';

// Simple color hash for user tags
function getUserTagColor(username) {
  // Generate a pastel color based on username hash
  let hash = 0;
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = Math.abs(hash) % 360;
  return `hsl(${h}, 70%, 85%)`;
}

const UserTag = ({ username, color, textColor }) => (
  <Link
    to={`/users/${username}`}
    className="user-tag"
    style={{ backgroundColor: color, color: textColor }}
    title={username}
  >
    {username}
  </Link>
);

const PhdThesisPage = () => {
  const [theses, setTheses] = useState([]);
  const [usersWithoutTheses, setUsersWithoutTheses] = useState([]);
  const [supervisorUsage, setSupervisorUsage] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentUsageTimestamp, setCurrentUsageTimestamp] = useState(null);
  const [gpuHoursMap, setGpuHoursMap] = useState({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch all data in parallel
        const [thesesData, usersData, currentUsageData, allGpuHours] = await Promise.all([
          fetchAllTheses(),
          getAllUsers(),
          getCurrentUsageAll(),
          api.getAllUsersGpuHours()
        ]);

        setTheses(thesesData.current_theses || []);
        setGpuHoursMap(allGpuHours || {});

        // Create a map of users to their supervisors
        const userToSupervisors = new Map();
        // Create a set of all supervisors
        const supervisors = new Set();
        
        // First, identify all supervisors from theses
        thesesData.all_theses.forEach(thesis => {
          thesis.supervisors?.forEach(supervisor => {
            supervisors.add(supervisor);
          });
        });

        // Map users to their supervisors
        thesesData.all_theses.forEach(thesis => {
          thesis.students?.forEach(student => {
            if (thesis.supervisors && thesis.supervisors.length > 0) {
              userToSupervisors.set(student, thesis.supervisors);
            }
          });
        });

        // Process current usage data
        const supervisorToUsage = new Map();
        const supervisorToUsers = new Map();

        // Initialize supervisor maps with all known supervisors
        supervisors.forEach(supervisor => {
          supervisorToUsage.set(supervisor, {
            cpus: 0,
            memory: 0,
            gpus: 0,
            gpu_hours: 0,
            users: new Set([supervisor]) // Include supervisor in their own user list
          });
        });

        // Add "nosupervisor" category
        supervisorToUsage.set('nosupervisor', {
          cpus: 0,
          memory: 0,
          gpus: 0,
          gpu_hours: 0,
          users: new Set()
        });

        // Build a map of user -> gpu_hours from allGpuHours
        const userToGpuHours = allGpuHours || {};

        // Process each user's current usage
        currentUsageData.usage?.forEach(usage => {
          const username = usage.user;
          const userRole = usersData.find(u => u.username === username)?.user_role;
          let gpu_hours = userToGpuHours[username] || 0;
          // Skip if no usage
          if (!usage.total_cpus && !usage.total_memory_gb && !usage.total_gpus && !gpu_hours) {
            return;
          }

          let userSupervisors = userToSupervisors.get(username);

          if (supervisors.has(username)) {
            // User is a supervisor - add their usage to their own total
            const data = supervisorToUsage.get(username);
            data.cpus += usage.total_cpus;
            data.memory += usage.total_memory_gb;
            data.gpus += usage.total_gpus;
            data.gpu_hours += gpu_hours;
          } else if (userSupervisors && userSupervisors.length > 0) {
            // User has supervisors - split usage among them
            const splitFactor = 1 / userSupervisors.length;
            userSupervisors.forEach(supervisor => {
              const data = supervisorToUsage.get(supervisor);
              data.cpus += usage.total_cpus * splitFactor;
              data.memory += usage.total_memory_gb * splitFactor;
              data.gpus += usage.total_gpus * splitFactor;
              data.gpu_hours += gpu_hours * splitFactor;
              data.users.add(username);
            });
          } else if (userRole?.toLowerCase() !== 'staff') {
            // User has no supervisor and is not staff - add to nosupervisor
            const data = supervisorToUsage.get('nosupervisor');
            data.cpus += usage.total_cpus;
            data.memory += usage.total_memory_gb;
            data.gpus += usage.total_gpus;
            data.gpu_hours += gpu_hours;
            data.users.add(username);
          }
        });

        // Convert the map to an array for display
        const supervisorUsageArray = Array.from(supervisorToUsage.entries())
          .map(([supervisor, data]) => ({
            supervisor,
            cpus: Math.round(data.cpus * 10) / 10, // Round to 1 decimal
            memory: Math.round(data.memory * 10) / 10,
            gpus: Math.round(data.gpus * 10) / 10,
            gpu_hours: Math.round(data.gpu_hours * 100) / 100,
            users: Array.from(data.users).sort().join(', ')
          }))
          .filter(data => data.cpus > 0 || data.memory > 0 || data.gpus > 0 || data.gpu_hours > 0) // Only show supervisors with usage
          .sort((a, b) => b.gpus - a.gpus); // Sort by GPU usage

        setSupervisorUsage(supervisorUsageArray);
        setCurrentUsageTimestamp(currentUsageData.timestamp);

        // Get all unique usernames from theses (both students and supervisors)
        const thesisUsers = new Set();
        thesesData.all_theses.forEach(thesis => {
          thesis.students?.forEach(student => thesisUsers.add(student));
          thesis.supervisors?.forEach(supervisor => thesisUsers.add(supervisor));
        });

        // Get users who are currently using resources
        const activeUsers = new Set(
          currentUsageData.usage?.map(user => user.user) || []
        );

        // Filter users to find those without theses who are currently using resources
        const usersWithoutThesesAndActive = usersData.filter(user => {
          // Skip staff/supervisors
          if (user.user_role?.toLowerCase() === 'staff') return false;
          // Include only users who:
          // 1. Don't have a thesis
          // 2. Are currently using resources
          return !thesisUsers.has(user.username) && activeUsers.has(user.username);
        });

        setUsersWithoutTheses(usersWithoutThesesAndActive);
        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to fetch data.');
        setTheses([]);
        setUsersWithoutTheses([]);
        setSupervisorUsage([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="phd-thesis-page">
      {/* 1. View Logs and Emails Button */}
      <div style={{ display: 'flex', justifyContent: 'center', margin: '2rem 0 2rem 0' }}>
        <Link to="/tasks" className="btn btn-primary btn-lg" style={{ fontSize: '1.3em', padding: '1em 2.5em', background: '#1976d2', color: '#fff', borderRadius: '2em', fontWeight: 600, boxShadow: '0 2px 8px #1976d233', border: 'none' }}>
          View Logs and Emails
        </Link>
      </div>

      {/* 2. Active Reservations */}
      <ActiveReservations />

      {/* 3. Announcements (uncomment if available) */}
      {/* <Announcements /> */}

      {/* 4. Resource Usage by Supervisor (collapsible) */}
      <CollapsibleSection title="Resource Usage by Supervisor" defaultOpen={true}>
        {supervisorUsage.length > 0 ? (
          <>
            {/* Last updated timestamp */}
            {currentUsageTimestamp && (
              <div style={{ color: '#888', fontSize: '0.95em', marginBottom: '0.5em' }}>
                Last updated: {new Date(currentUsageTimestamp.replace(' ', 'T')).toLocaleString()}<br />
                {(() => {
                  const now = new Date();
                  const last = new Date(currentUsageTimestamp.replace(' ', 'T'));
                  const diffMs = now - last;
                  const hours = diffMs / 3600000;
                  return `(${hours.toFixed(1)} hours ago)`;
                })()}
              </div>
            )}
            <div className="card mb-4" style={{ boxShadow: 'none', border: 'none', marginBottom: 0 }}>
              <div className="card-body">
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Supervisor</th>
                        <th>Total CPUs</th>
                        <th>Total Memory (GB)</th>
                        <th>Total GPUs</th>
                        <th>Total GPU Hours</th>
                        <th>Associated Users</th>
                      </tr>
                    </thead>
                    <tbody>
                      {supervisorUsage.map((usage, idx) => (
                        <tr key={idx}>
                          <td>{usage.supervisor === 'nosupervisor' ? 'No Supervisor' : usage.supervisor}</td>
                          <td>{usage.cpus}</td>
                          <td>{usage.memory}</td>
                          <td>{usage.gpus}</td>
                          <td>{usage.gpu_hours}</td>
                          <td style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                            {usage.users.split(', ').map((username) => (
                              <UserTag key={username} username={username} color="#1976d2" textColor="#fff" />
                            ))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </>
        ) : <p>No supervisor usage data available.</p>}
      </CollapsibleSection>

      {/* 5. Current Usage Table (collapsible) */}
      <CollapsibleSection title="Current Resource Usage" defaultOpen={false}>
        <CurrentUsage />
      </CollapsibleSection>

      {/* 6. Active Users Without Registered Theses (collapsible) */}
      <CollapsibleSection title="Active Users Without Registered Theses" defaultOpen={true}>
        {usersWithoutTheses.length > 0 ? (
          <div className="card mb-4" style={{ boxShadow: 'none', border: 'none', marginBottom: 0 }}>
            <div className="card-body">
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Username</th>
                      <th>Full Name</th>
                      <th>Role</th>
                      <th>Affiliation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usersWithoutTheses.map((user, idx) => (
                      <tr key={idx}>
                        <td>{user.username}</td>
                        <td>{user.full_name || 'N/A'}</td>
                        <td>{user.user_role || 'N/A'}</td>
                        <td>{user.user_affiliation || 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : <p>No active users without registered theses.</p>}
      </CollapsibleSection>

      {/* 7. Current Theses (collapsible) */}
      <CollapsibleSection title="Current Theses" defaultOpen={false}>
        <div className="card" style={{ boxShadow: 'none', border: 'none', marginBottom: 0 }}>
          <div className="card-body">
            {theses.length > 0 ? (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th></th>
                      <th>Thesis Title</th>
                      <th>Semester</th>
                      <th>Supervisors</th>
                      <th>Students</th>
                      <th>Student E-mails</th>
                    </tr>
                  </thead>
                  <tbody>
                    {theses.map((thesis, idx) => (
                      <tr key={idx}>
                        <td>
                          {thesis.icon_url ? (
                            <img src={thesis.icon_url} alt={thesis.title} className="thesis-icon" />
                          ) : (
                            <div className="thesis-icon-placeholder">No Image</div>
                          )}
                        </td>
                        <td>{thesis.title}</td>
                        <td>{thesis.semester}</td>
                        <td>{thesis.supervisors && thesis.supervisors.length > 0 ? thesis.supervisors.join(', ') : 'N/A'}</td>
                        <td>{thesis.students && thesis.students.length > 0 ? thesis.students.join(', ') : 'N/A'}</td>
                        <td>{thesis.student_emails && thesis.student_emails.length > 0 ? thesis.student_emails.join(', ') : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <p>No current theses found.</p>}
          </div>
        </div>
      </CollapsibleSection>
    </div>
  );
};

export default PhdThesisPage; 