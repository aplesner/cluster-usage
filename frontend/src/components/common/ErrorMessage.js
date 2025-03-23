import React from 'react';

const ErrorMessage = ({ message }) => {
  return (
    <div className="alert alert-error">
      <p>{message || 'An error occurred while fetching data. Please try again later.'}</p>
    </div>
  );
};

export default ErrorMessage;

