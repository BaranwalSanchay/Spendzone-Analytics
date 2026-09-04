
import { useState } from "react";
import { useLocation } from "react-router-dom";
import DateRangePicker from "./DateRangePicker";
import DatasetSelector from "./DatasetSelector";
import { Button } from "@/components/ui/button";
import { Download, Share2, RefreshCw, SlidersHorizontal, Globe, Database, Laptop } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useDashboard } from "@/contexts/DashboardContext";
import { toast } from "sonner";

const getSectionTitle = (pathname: string): string => {
  const pathSegments = pathname.split("/");
  const lastSegment = pathSegments[pathSegments.length - 1];

  const titles: Record<string, string> = {
    "executive-summary": "Executive Summary",
    "business-context": "Business Context",
    "marketing-performance": "Marketing Performance",
    "performance-drivers": "Performance Drivers",
    "marketing-roi": "Marketing ROI",
    "budget-allocation": "Budget Allocation",
    "implementation": "Implementation",
    "appendix": "Appendix",
  };

  return titles[lastSegment] || "Dashboard";
};

const DashboardHeader = () => {
  const location = useLocation();
  const { hasData, resetFilters } = useDashboard();
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const sectionTitle = getSectionTitle(location.pathname);

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

  return (
    <div className="border-b p-3 bg-white dark:bg-gray-800">
      <div className="flex flex-col gap-2">
        <h1 className="text-xl font-semibold">{sectionTitle}</h1>
        
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center justify-between">
          <div className="flex flex-wrap gap-2">
            <Sheet open={isFilterOpen} onOpenChange={setIsFilterOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="sm" className="gap-1">
                  <SlidersHorizontal className="h-4 w-4" />
                  <span>Filters</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="right">
                <SheetHeader>
                  <SheetTitle>Dashboard Filters</SheetTitle>
                </SheetHeader>
                <div className="py-4">
                  <div className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      Apply filters to customize your dashboard view.
                    </p>

                    <div className="space-y-2">
                      <h3 className="text-sm font-medium">Medium</h3>
                      <Button variant="outline" size="sm" className="w-full justify-start text-left">
                        <Globe className="h-4 w-4 mr-2" />
                        All
                      </Button>
                    </div>

                    <div className="space-y-2">
                      <h3 className="text-sm font-medium">Device Category</h3>
                      <Button variant="outline" size="sm" className="w-full justify-start text-left">
                        <Laptop className="h-4 w-4 mr-2" />
                        All Devices
                      </Button>
                    </div>

                    <div className="space-y-2">
                      <h3 className="text-sm font-medium">Country</h3>
                      <Button variant="outline" size="sm" className="w-full justify-start text-left">
                        <Globe className="h-4 w-4 mr-2" />
                        All Countries
                      </Button>
                    </div>

                    <div className="space-y-2">
                      <h3 className="text-sm font-medium">Hostname</h3>
                      <Button variant="outline" size="sm" className="w-full justify-start text-left">
                        <Database className="h-4 w-4 mr-2" />
                        All Hostnames
                      </Button>
                    </div>

                    <div className="pt-4">
                      <Button onClick={() => {
                        resetFilters();
                        setIsFilterOpen(false);
                        toast.success("Filters reset");
                      }} variant="secondary" className="w-full">
                        Reset Filters
                      </Button>
                    </div>
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
          </div>

          <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
            <DateRangePicker />
            <DatasetSelector />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardHeader;
