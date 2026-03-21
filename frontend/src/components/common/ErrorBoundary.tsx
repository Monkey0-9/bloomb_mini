import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Terminal Error Captured:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex flex-col items-center justify-center min-h-[400px] border border-red-900/50 bg-black p-8 rounded-lg">
          <div className="w-16 h-16 mb-6 text-red-500">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-red-100 mb-2 font-mono uppercase tracking-widest">Terminal Handler Fault</h2>
          <p className="text-gray-400 text-center max-w-md font-sans text-sm mb-6">
            A critical fault occurred in the UI renderer. The system is operating in degraded mode.
          </p>
          <button 
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-red-900/20 hover:bg-red-900/40 border border-red-700/50 text-red-100 font-mono text-xs uppercase transition-all"
          >
            Re-Initialize Terminal
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
