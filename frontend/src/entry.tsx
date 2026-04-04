import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './TerminalApp';
import { ErrorBoundary } from './components/ErrorBoundary';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary widgetName="SatTrade Terminal">
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
