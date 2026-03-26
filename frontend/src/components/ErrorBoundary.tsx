import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
  widgetName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Enterprise production-grade Error Boundary.
 * Catches UI rendering errors locally to prevent the entire terminal from crashing,
 * a requirement for mission-critical Bloomberg-style dashboards.
 */
export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`Uncaught error in widget ${this.props.widgetName || "Unknown"}:`, error, errorInfo);
    // Future: Send to Sentry or Datadog here
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center p-6 bg-red-950/20 border border-red-900/50 rounded-lg h-full min-h-[150px]">
          <AlertTriangle className="w-8 h-8 text-red-500 mb-3" />
          <h3 className="text-red-400 font-semibold mb-1">
            {this.props.widgetName ? `${this.props.widgetName} Failed` : "Widget Error"}
          </h3>
          <p className="text-red-300/60 text-xs mb-4 text-center">
            {this.state.error?.message || "An unexpected rendering error occurred."}
          </p>
          <button
            onClick={this.handleReset}
            className="flex items-center gap-2 px-3 py-1.5 text-xs bg-red-900/40 hover:bg-red-900/60 text-red-200 rounded transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            Reload Widget
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
