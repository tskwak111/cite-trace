import React from 'react';

export const LimitationNotice: React.FC<{ message: string }> = ({ message }) => {
  return <div className="limitation-notice">{message}</div>;
};
