
import React from 'react';

export const Logo: React.FC = () => {
  return (
    <div className="flex items-center gap-2">
      <div className="h-8 w-8 bg-gradient-to-br from-teal-400 to-teal-600 rounded-md flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
          <rect x="2" y="2" width="8" height="8" rx="1"></rect>
          <path d="M14 2l6 6-6 6"></path>
          <rect x="2" y="14" width="8" height="8" rx="1"></rect>
        </svg>
      </div>
      <span className="font-semibold text-lg tracking-tight">Spendzone</span>
    </div>
  );
};
