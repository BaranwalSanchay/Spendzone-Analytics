
import React, { ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tooltip } from '@/components/ui/tooltip';
import { TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { InfoIcon, DownloadIcon, ExpandIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ChartCardProps {
  title: string;
  children: ReactNode;
  tooltip?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'auto';
  height?: number | string;
  allowDownload?: boolean;
  allowExpand?: boolean;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  children,
  tooltip,
  className = '',
  size = 'md',
  height = 300,
  allowDownload = true,
  allowExpand = true,
}) => {
  // Define height based on size
  const getHeight = () => {
    if (typeof height === 'number' || typeof height === 'string') return height;
    
    switch (size) {
      case 'sm': return 200;
      case 'md': return 300;
      case 'lg': return 400;
      case 'auto': return 'auto';
      default: return 300;
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="p-4 flex flex-row items-center justify-between">
        <CardTitle className="text-md font-medium flex items-center">
          {title}
          {tooltip && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <InfoIcon className="h-4 w-4 ml-2 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs text-sm">{tooltip}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </CardTitle>
        
        <div className="flex space-x-1">
          {allowDownload && (
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <DownloadIcon className="h-4 w-4" />
            </Button>
          )}
          {allowExpand && (
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ExpandIcon className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-0">
        <div style={{ height: getHeight(), width: '100%' }}>
          {children}
        </div>
      </CardContent>
    </Card>
  );
};
