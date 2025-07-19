// API service for making requests to the backend
const API_URL = process.env.REACT_APP_API_URL || '/api';

/**
 * Fetch data from the API
 * @param {string} endpoint - API endpoint to fetch from
 * @returns {Promise} - Promise with the JSON response
 */
async function fetchData(endpoint) {
  try {
    const response = await fetch(`${API_URL}${endpoint}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API fetch error:', error);
    throw error;
  }
}

/**
 * Get all users with their basic stats
 * @returns {Promise} - Promise with the users data
 */
export const getUsers = () => fetchData('/users');

/**
 * Get overall database statistics
 * @returns {Promise} - Promise with the stats data
 */
export const getStats = () => fetchData('/stats');

/**
 * Get all machines
 * @returns {Promise} - Promise with the machines data
 */
export const getMachines = () => fetchData('/machines');

/**
 * Get detailed usage statistics for a specific user
 * @param {string} username - Username to get data for
 * @returns {Promise} - Promise with the user usage data
 */
export const getUserUsage = (username) => fetchData(`/usage/user/${username}`);

/**
 * Get detailed usage statistics for a specific machine
 * @param {string} machineName - Machine name to get data for
 * @returns {Promise} - Promise with the machine usage data
 */
export const getMachineUsage = (machineName) => fetchData(`/usage/machine/${machineName}`);

/**
 * Get time-based usage statistics
 * @returns {Promise} - Promise with the time usage data
 */
export const getTimeUsage = () => fetchData('/usage/time');

/**
 * Get size distribution statistics
 * @returns {Promise} - Promise with the size distribution data
 */
export const getSizeDistribution = () => fetchData('/usage/size');

/**
 * Get time-based usage statistics for a specific user
 * @param {string} username - Username to get time stats for
 * @returns {Promise} - Promise with the user time usage data
 */
export const getUserTimeStats = (username) => fetchData(`/usage/user/${username}/time`);

/**
 * Get top users by IO operations for most recent logs
 * @param {number} logCount - Number of recent logs to consider
 * @param {number} userCount - Number of top users to return
 * @returns {Promise} - Promise with the top users data
 */
export const getTopUsersRecent = (logCount = 5, userCount = 10) => 
  fetchData(`/top-users/recent?logs=${logCount}&users=${userCount}`);

/**
 * Get historic usage data with top N users for each log entry
 * @param {number} topN - Number of top users to return per log entry
 * @returns {Promise} - Promise with the historic usage data
 */
export const getHistoricUsage = (topN = 10) => 
  fetchData(`/usage/historic?top_n=${topN}`);

/**
 * Get periodic task logs with pagination
 * @param {number} page - Page number (1-based)
 * @param {number} limit - Number of items per page
 * @returns {Promise} - Promise with the task logs data and pagination info
 */
export const getTaskLogs = (page = 1, limit = 20) => 
  fetchData(`/task-logs?page=${page}&limit=${limit}`);

/**
 * Get email notifications with pagination
 * @param {number} page - Page number (1-based)
 * @param {number} limit - Number of items per page
 * @returns {Promise} - Promise with the email notifications data and pagination info
 */
export const getEmailNotifications = (page = 1, limit = 20) => 
  fetchData(`/email-notifications?page=${page}&limit=${limit}`);

/**
 * Get number of sent emails to each user for a given time range
 * @param {string} startTime - Start of the time range (ISO string)
 * @param {string} endTime - End of the time range (ISO string)
 * @returns {Promise} - Promise with the counts object { counts: { username: count, ... } }
 */
export const getEmailCountsByUser = (startTime, endTime) =>
  fetchData(`/email-notifications/counts?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`);

/** * Fetch thesis details for a specific user
 * @param {string} username - Username to get thesis details for
 * @returns {Promise} - Promise with the thesis details data
 */
export const fetchThesisDetails = (username) =>
  fetchData(`/users/${username}/thesis-details`);

const api = {
  getUsers,
  getStats,
  getMachines,
  getUserUsage,
  getMachineUsage,
  getTimeUsage,
  getSizeDistribution,
  getUserTimeStats,
  getTopUsersRecent,
  getHistoricUsage,
  getTaskLogs,
  getEmailNotifications,
  getEmailCountsByUser,
  fetchThesisDetails,
  async getActiveCalendarEvents() {
    const response = await fetch('/api/calendar/active');
    if (!response.ok) {
      throw new Error('Failed to fetch active calendar events');
    }
    return response.json();
  },
  async getCurrentUsage() {
    const response = await fetch('/api/calendar/current-usage');
    if (!response.ok) {
      throw new Error('Failed to fetch current usage data');
    }
    return response.json();
  },
  async getUserOverview(username) {
    const response = await fetch(`${API_URL}/users/${username}/overview`);
    if (!response.ok) {
      throw new Error('Failed to fetch user overview data');
    }
    return response.json();
  },
  async getCalendarLastRefresh() {
    const response = await fetch('/api/calendar/last-refresh');
    if (!response.ok) {
      throw new Error('Failed to fetch last calendar refresh time');
    }
    return response.json();
  },
  async getUserGpuHours(username) {
    const response = await fetch(`/api/users/${username}/gpu-hours`);
    if (!response.ok) {
      throw new Error('Failed to fetch user GPU hours');
    }
    return response.json();
  },
  async getAllUsersGpuHours() {
    const response = await fetch('/api/users/gpu-hours');
    if (!response.ok) {
      throw new Error('Failed to fetch all users GPU hours');
    }
    return response.json();
  },
  async getUsersEmailedLast12h() {
    const response = await fetch('/api/users/emails-last-12h');
    if (!response.ok) {
      throw new Error('Failed to fetch users emailed in last 12 hours');
    }
    return response.json();
  },
  async getUserThesisSupervisors(username) {
    const response = await fetch(`/api/users/${username}/thesis-supervisors`);
    if (!response.ok) {
      throw new Error('Failed to fetch thesis and supervisor info');
    }
    return response.json();
  },
  async getAllThesesSupervisors() {
    const response = await fetch('/api/theses-supervisors');
    if (!response.ok) {
      throw new Error('Failed to fetch all theses and supervisors');
    }
    return response.json();
  }
};

export default api;

