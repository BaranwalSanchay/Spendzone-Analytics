import React, { useState, useContext } from 'react';
import { DateRangePicker } from './ui/date-range-picker';
import { DateRange } from 'react-day-picker';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { 
  Download, 
  Share2, 
  RefreshCw, 
  SlidersHorizontal, 
  Upload,
  Filter,
  Database
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetFooter
} from "@/components/ui/sheet";
import { toast } from "sonner";
import { useDashboard } from "@/contexts/DashboardContext";
import { motion } from "framer-motion";

// Define dataset interface if not already imported
interface Dataset {
  id: string;
  name: string;
  size: number;
  uploadDate: Date;
  description?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  filters?: {
    label: string;
    options: { value: string; label: string }[];
    onChange: (value: string) => void;
    value: string;
  }[];
  hasData?: boolean;
  onResetFilters?: () => void;
  showDatasetSelector?: boolean;
  /** Controlled date range — pass this + onDateRangeChange to filter a page's own data. */
  dateRange?: DateRange | undefined;
  onDateRangeChange?: (range: DateRange | undefined) => void;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  filters = [],
  hasData = true,
  onResetFilters = () => {},
  showDatasetSelector = true,
  dateRange,
  onDateRangeChange
}) => {
  // Falls back to uncontrolled local state for pages that don't need to react to the date range.
  const [internalDate, setInternalDate] = React.useState<DateRange | undefined>({
    from: new Date(2023, 0, 1),
    to: new Date(2023, 11, 31)
  });
  const date = dateRange !== undefined ? dateRange : internalDate;
  const setDate = onDateRangeChange ?? setInternalDate;
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string>>({});
  
  // Use dashboard context if available, otherwise use mock data
  let dashboardData;
  let setActiveDataset;
  
  try {
    const dashboard = useDashboard();
    dashboardData = dashboard.data;
    setActiveDataset = dashboard.setActiveDataset;
  } catch (error) {
    // If context is not available, use mock data
    dashboardData = {
      datasets: [
        { 
          id: "1", 
          name: "Marketing Campaign 2023", 
          size: 1024000,
          uploadDate: new Date(2023, 5, 15) 
        },
        { 
          id: "2", 
          name: "Q4 Sales Data", 
          size: 2048000,
          uploadDate: new Date(2023, 11, 10) 
        }
      ],
      activeDatasetId: "1"
    };
    setActiveDataset = (id: string) => {
      console.log(`Selected dataset: ${id}`);
      toast.success(`Dataset changed to ${dashboardData.datasets.find(d => d.id === id)?.name}`);
    };
  }

  const formatBytes = (bytes: number, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  };

  const handleFilterChange = (filterLabel: string, value: string) => {
    setSelectedFilters(prev => ({
      ...prev,
      [filterLabel]: value
    }));
    
    // Call the onChange handler from the filter props
    const filter = filters.find(f => f.label === filterLabel);
    if (filter && filter.onChange) {
      filter.onChange(value);
    }
  };

  const handleReset = () => {
    setSelectedFilters({});
    onResetFilters();
    setIsFilterOpen(false);
    toast.success("Filters reset");
  };

  const handleDownload = () => {
    if (!hasData) {
      toast.error("No data available to download");
      return;
    }
    toast.success("Download started");
  };

  const handleShare = () => {
    if (!hasData) {
      toast.error("No data available to share");
      return;
    }
    toast.success("Dashboard link copied to clipboard");
  };

  const handleRefresh = () => {
    if (!hasData) {
      toast.error("No data available to refresh");
      return;
    }
    toast.success("Dashboard refreshed");
  };

  const handleFileUpload = () => {
    // This is a placeholder for file upload functionality
    toast.success("File upload functionality would open here");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="pb-4 border-b mb-6">
        <div className="flex flex-col md:flex-row justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">{title}</h1>
            {subtitle && <p className="text-muted-foreground">{subtitle}</p>}
          </div>
          <div className="mt-4 md:mt-0 flex flex-col sm:flex-row gap-2">
            {/* Dataset Selector */}
            {showDatasetSelector && (
              <div className="w-full sm:w-[300px]">
                <Select
                  value={dashboardData.activeDatasetId || undefined}
                  onValueChange={setActiveDataset}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select dataset">
                      <div className="flex items-center gap-2">
                        <Database className="h-4 w-4" />
                        <span>
                          {dashboardData.datasets.find(d => d.id === dashboardData.activeDatasetId)?.name || "Select dataset"}
                        </span>
                      </div>
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {dashboardData.datasets.length === 0 ? (
                      <div className="py-2 px-2 text-sm text-muted-foreground">
                        No datasets available
                      </div>
                    ) : (
                      dashboardData.datasets.map((dataset: Dataset) => (
                        <SelectItem key={dataset.id} value={dataset.id}>
                          <div className="flex flex-col">
                            <span className="font-medium">{dataset.name}</span>
                            <span className="text-xs text-muted-foreground">
                              {formatBytes(dataset.size)} • Uploaded {formatDate(dataset.uploadDate)}
                            </span>
                          </div>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Date Range Picker */}
            <DateRangePicker 
              value={date} 
              onChange={setDate} 
            />
          </div>
        </div>
        
        {/* Action buttons */}
        <div className="flex flex-wrap gap-2 mt-4">
          <Sheet open={isFilterOpen} onOpenChange={setIsFilterOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1">
                <SlidersHorizontal className="h-4 w-4" />
                <span>Filters</span>
                {Object.keys(selectedFilters).length > 0 && (
                  <span className="ml-1 inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
                    {Object.keys(selectedFilters).length}
                  </span>
                )}
              </Button>
            </SheetTrigger>
            <SheetContent side="right">
              <SheetHeader>
                <SheetTitle>{title} Filters</SheetTitle>
              </SheetHeader>
              
              <div className="py-4">
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Apply filters to customize your {title.toLowerCase()} view.
                  </p>

                  {filters.length === 0 ? (
                    <div className="text-sm text-muted-foreground">
                      No filters available for this page.
                    </div>
                  ) : (
                    filters.map((filter, index) => (
                      <div key={index} className="space-y-2">
                        <h3 className="text-sm font-medium">{filter.label}</h3>
                        <Select 
                          value={selectedFilters[filter.label] || filter.value} 
                          onValueChange={(value) => handleFilterChange(filter.label, value)}
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder={`Select ${filter.label}`} />
                          </SelectTrigger>
                          <SelectContent>
                            {filter.options.map((option) => (
                              <SelectItem key={option.value} value={option.value}>
                                {option.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ))
                  )}
                  
                  <SheetFooter className="pt-4 mt-4 border-t">
                    <Button onClick={handleReset} variant="secondary" className="w-full">
                      Reset Filters
                    </Button>
                  </SheetFooter>
                </div>
              </div>
            </SheetContent>
          </Sheet>

          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={handleDownload}
            disabled={!hasData}
          >
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Export</span>
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={handleShare}
            disabled={!hasData}
          >
            <Share2 className="h-4 w-4" />
            <span className="hidden sm:inline">Share</span>
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={handleRefresh}
            disabled={!hasData}
          >
            <RefreshCw className="h-4 w-4" />
            <span className="hidden sm:inline">Refresh</span>
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={handleFileUpload}
          >
            <Upload className="h-4 w-4" />
            <span className="hidden sm:inline">Upload</span>
          </Button>
        </div>
        
        {/* Display active filters */}
        {Object.keys(selectedFilters).length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {Object.entries(selectedFilters).map(([filterName, value]) => {
              const filter = filters.find(f => f.label === filterName);
              const option = filter?.options.find(o => o.value === value);
              
              if (!option) return null;
              
              return (
                <div 
                  key={filterName} 
                  className="inline-flex items-center bg-muted rounded-full px-3 py-1 text-sm"
                >
                  <span className="font-medium mr-1">{filterName}:</span>
                  <span>{option.label}</span>
                  <button 
                    className="ml-2 text-muted-foreground hover:text-foreground"
                    onClick={() => {
                      const newFilters = {...selectedFilters};
                      delete newFilters[filterName];
                      setSelectedFilters(newFilters);
                    }}
                  >
                    ×
                  </button>
                </div>
              );
            })}
            
            <button 
              className="text-sm text-primary hover:underline"
              onClick={handleReset}
            >
              Clear all
            </button>
          </div>
        )}
      </div>
    </motion.div>
  );
};
