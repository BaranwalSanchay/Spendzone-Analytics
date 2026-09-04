
import React from 'react';
import { 
  CartesianGrid, 
  Line, 
  LineChart, 
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { InfoIcon, ZoomInIcon, DownloadIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface MarketingChartProps {
  title: string;
  description?: string;
  data: any[];
  type: 'line' | 'bar' | 'pie' | 'horizontal-bar';
  dataKeys: string[];
  xAxisKey?: string;
  height?: number;
  colors?: string[];
  percentage?: boolean;
  stacked?: boolean;
  showDownload?: boolean;
  showZoom?: boolean;
  className?: string;
}

export const MarketingChart: React.FC<MarketingChartProps> = ({
  title,
  description,
  data,
  type,
  dataKeys,
  xAxisKey = 'name',
  height = 300,
  colors = ['#38B2AC', '#4FD1C5', '#81E6D9', '#2D3748', '#4A5568', '#F6AD55', '#F6E05E', '#9AE6B4'],
  percentage = false,
  stacked = false,
  showDownload = true,
  showZoom = true,
  className,
}) => {
  const renderTooltipValue = (value: any) => {
    if (percentage) return `${value}%`;
    
    if (typeof value === 'number') {
      if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(2)}M`;
      } else if (value >= 1000) {
        return `$${(value / 1000).toFixed(1)}K`;
      } else {
        return `$${value}`;
      }
    }
    
    return value;
  };

  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={xAxisKey} />
              <YAxis />
              <Tooltip 
                formatter={(value: any) => renderTooltipValue(value)} 
              />
              <Legend />
              {dataKeys.map((key, index) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={colors[index % colors.length]}
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
        
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={xAxisKey} />
              <YAxis />
              <Tooltip 
                formatter={(value: any) => renderTooltipValue(value)} 
              />
              <Legend />
              {dataKeys.map((key, index) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={colors[index % colors.length]}
                  stackId={stacked ? "a" : undefined}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
        
      case 'horizontal-bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart 
              layout="vertical" 
              data={data}
              margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
              <XAxis type="number" />
              <YAxis dataKey={xAxisKey} type="category" width={100} />
              <Tooltip 
                formatter={(value: any) => renderTooltipValue(value)}
              />
              <Legend />
              {dataKeys.map((key, index) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={colors[index % colors.length]}
                  label={{ 
                    position: 'right',
                    formatter: (value: any) => renderTooltipValue(value)
                  }}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
        
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey={dataKeys[0]}
                nameKey={xAxisKey}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: any) => renderTooltipValue(value)} />
            </PieChart>
          </ResponsiveContainer>
        );
        
      default:
        return <div>Chart type not supported</div>;
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="p-4 flex flex-row items-center justify-between">
        <div className="flex items-center">
          <CardTitle className="text-md font-medium">{title}</CardTitle>
          {description && (
            <TooltipProvider>
              <UITooltip>
                <TooltipTrigger asChild>
                  <InfoIcon className="ml-2 h-4 w-4 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs text-sm">{description}</p>
                </TooltipContent>
              </UITooltip>
            </TooltipProvider>
          )}
        </div>
        
        <div className="flex space-x-1">
          {showDownload && (
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <DownloadIcon className="h-4 w-4" />
            </Button>
          )}
          {showZoom && (
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ZoomInIcon className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-0">
        {renderChart()}
      </CardContent>
    </Card>
  );
};
