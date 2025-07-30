// Utility to format a date string in CET/CEST (Europe/Berlin)
export default function formatCETDate(dateString, options = {}) {
  if (!dateString) return '';
  const date = new Date(dateString);
  // Default options for full date and time
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/Berlin',
  };
  return date.toLocaleString('en-GB', { ...defaultOptions, ...options });
} 