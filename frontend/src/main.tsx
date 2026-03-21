import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './TerminalApp';
import ErrorBoundary from './components/common/ErrorBoundary';
import './index.css';
import './styles/terminal.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
