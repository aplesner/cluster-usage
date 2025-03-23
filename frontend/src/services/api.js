// API service for making requests to the backend
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

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

// Update the API object to include the new function
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
  getHistoricUsage
};


export default api;

