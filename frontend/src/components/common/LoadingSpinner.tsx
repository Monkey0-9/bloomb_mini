import React from 'react';

interface Props {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

const LoadingSpinner: React.FC<Props> = ({ label = 'Initializing Terminal...', size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-2',
    lg: 'w-12 h-12 border-3'
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 space-y-4 font-mono">
      <div className={`${sizeClasses[size]} border-t-accent-primary border-r-transparent border-b-accent-primary border-l-transparent rounded-full animate-rotate-terminal`}></div>
      {label && (
        <div className="text-[10px] uppercase tracking-[0.2em] text-accent-primary/60 animate-pulse">
          {label}
        </div>
      )}
    </div>
  );
};

export default LoadingSpinner;
