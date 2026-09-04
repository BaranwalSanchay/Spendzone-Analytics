import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowDownIcon, ArrowUpIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  title: string;
  value: string | number;
  trend?: {
    value: number;
    isPositive: boolean;
    text?: string;
  };
  icon?: React.ReactNode;
  className?: string;
  iconBackground?: string;
  bgGradient?: string;
  compact?: boolean;
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  trend,
  icon,
  className,
  iconBackground,
  bgGradient = "linear-gradient(90deg, rgb(20, 184, 166) 0%, rgb(45, 212, 191) 100%)",
  compact = false,
}) => {
  return (
    <Card 
      className={cn(
        "overflow-hidden",
        compact && "w-full",
        className
      )}
      style={
        bgGradient ? {
          background: bgGradient,
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
        } : undefined
      }
    >
      <CardContent className={cn("p-6", compact && "p-4")}>
        <div className="flex items-start justify-between">
          <div>
            <p className={cn(
              "text-sm font-medium",
              compact && "text-xs",
              bgGradient ? "text-white/90" : "text-muted-foreground"
            )}>{title}</p>
            <h3 className={cn(
              "text-2xl font-bold mt-1",
              compact && "text-xl",
              bgGradient && "text-white"
            )}>{value}</h3>
            
            {trend && (
              <div className={cn(
                "flex items-center mt-1 text-xs font-medium",
                compact && "text-[10px]",
                trend.isPositive ? "text-green-500" : "text-red-500",
                bgGradient && "text-white/90"
              )}>
                {trend.isPositive ? (
                  <ArrowUpIcon className="h-3 w-3 mr-1" />
                ) : (
                  <ArrowDownIcon className="h-3 w-3 mr-1" />
                )}
                <span>{trend.value}%</span>
                {trend.text && <span className={cn(
                  "ml-1",
                  bgGradient ? "text-white/70" : "text-muted-foreground"
                )}>{trend.text}</span>}
              </div>
            )}
          </div>
          
          {icon && (
            <div className={cn(
              "flex items-center justify-center rounded-full p-2",
              compact && "p-1.5",
              bgGradient ? "bg-white/10" : (iconBackground || "bg-primary/10")
            )}>
              {React.cloneElement(icon as React.ReactElement, {
                className: cn(
                  (icon as React.ReactElement).props.className,
                  compact && "h-4 w-4",
                  bgGradient && "text-white"
                )
              })}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
