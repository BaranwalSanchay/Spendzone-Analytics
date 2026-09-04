import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children: React.ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Catches rendering errors in its subtree (e.g. malformed lime_explanations.json
 * or other model-output payloads) and shows a fallback instead of a blank page.
 */
export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center gap-4 p-12 text-center">
          <AlertTriangle className="h-10 w-10 text-destructive" />
          <div>
            <h2 className="text-lg font-semibold">
              {this.props.fallbackTitle ?? 'Something went wrong'}
            </h2>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              This section couldn't be displayed, likely due to unexpected or malformed data.
              {this.state.error?.message ? ` (${this.state.error.message})` : ''}
            </p>
          </div>
          <Button onClick={this.handleReset} variant="outline">
            Try again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
