
import React from 'react';
import { BarChart3, PieChart, LineChart, TrendingUp } from 'lucide-react';

export const LoadingAnimation: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="relative w-20 h-20 mb-4">
        <div className="absolute inset-0 flex items-center justify-center animate-pulse-opacity" style={{ animationDelay: '0ms' }}>
          <BarChart3 className="w-12 h-12 text-marketing-primary" />
        </div>
        <div className="absolute inset-0 flex items-center justify-center animate-pulse-opacity" style={{ animationDelay: '500ms' }}>
          <PieChart className="w-12 h-12 text-marketing-secondary" />
        </div>
        <div className="absolute inset-0 flex items-center justify-center animate-pulse-opacity" style={{ animationDelay: '1000ms' }}>
          <LineChart className="w-12 h-12 text-marketing-accent" />
        </div>
        <div className="absolute inset-0 flex items-center justify-center animate-pulse-opacity" style={{ animationDelay: '1500ms' }}>
          <TrendingUp className="w-12 h-12 text-marketing-highlight" />
        </div>
      </div>
      <div className="text-xl font-medium text-marketing-primary">Generating report...</div>
      <div className="mt-2 text-sm text-muted-foreground">Analyzing data and compiling insights</div>
      <div className="mt-6 w-64 h-2 bg-muted rounded-full overflow-hidden">
        <div className="h-full bg-marketing-primary rounded-full animate-pulse" style={{ width: '70%' }}></div>
      </div>
    </div>
  );
};
