
import React, { createContext, useState, useContext, ReactNode } from "react";

export interface DataSet {
  id: string;
  name: string;
  description: string;
  dateRange: {
    start: Date;
    end: Date;
  };
  type: string;
  fileName: string;
  uploadDate: Date;
  size: number;
}

interface DashboardData {
  datasets: DataSet[];
  activeDatasetId: string | null;
  dateRange: {
    start: Date;
    end: Date;
  };
  filters: Record<string, any>;
}

interface DashboardContextType {
  data: DashboardData;
  isLoading: boolean;
  setDateRange: (start: Date, end: Date) => void;
  setActiveDataset: (datasetId: string) => void;
  addDataset: (dataset: Omit<DataSet, "id">) => void;
  removeDataset: (datasetId: string) => void;
  setFilter: (key: string, value: any) => void;
  resetFilters: () => void;
  hasData: boolean;
}

const defaultDateRange = {
  start: new Date(new Date().getFullYear(), 0, 1), // Jan 1 of current year
  end: new Date(),
};

const defaultContext: DashboardData = {
  datasets: [],
  activeDatasetId: null,
  dateRange: defaultDateRange,
  filters: {},
};

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export const DashboardProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [dashboardData, setDashboardData] = useState<DashboardData>(defaultContext);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // For demo purposes, add sample data if none exists
  React.useEffect(() => {
    if (dashboardData.datasets.length === 0) {
      const sampleDataset: Omit<DataSet, "id"> = {
        name: "ElectroMart Marketing Data 2023",
        description: "Annual marketing performance data for ElectroMart Canada",
        dateRange: {
          start: new Date(2023, 0, 1),
          end: new Date(2023, 11, 31),
        },
        type: "marketing",
        fileName: "electromart_marketing_2023.csv",
        uploadDate: new Date(2024, 3, 15),
        size: 1458000,
      };
      
      addDataset(sampleDataset);
    }
  }, []);

  const setDateRange = (start: Date, end: Date) => {
    setDashboardData((prev) => ({
      ...prev,
      dateRange: { start, end },
    }));
  };

  const setActiveDataset = (datasetId: string) => {
    setDashboardData((prev) => ({
      ...prev,
      activeDatasetId: datasetId,
    }));
  };

  const addDataset = (dataset: Omit<DataSet, "id">) => {
    const newDataset: DataSet = {
      ...dataset,
      id: `dataset-${Date.now()}`,
    };

    setDashboardData((prev) => {
      const newDatasets = [...prev.datasets, newDataset];
      return {
        ...prev,
        datasets: newDatasets,
        activeDatasetId: newDataset.id,
      };
    });
  };

  const removeDataset = (datasetId: string) => {
    setDashboardData((prev) => {
      const newDatasets = prev.datasets.filter((d) => d.id !== datasetId);
      return {
        ...prev,
        datasets: newDatasets,
        activeDatasetId: newDatasets.length > 0 ? newDatasets[0].id : null,
      };
    });
  };

  const setFilter = (key: string, value: any) => {
    setDashboardData((prev) => ({
      ...prev,
      filters: {
        ...prev.filters,
        [key]: value,
      },
    }));
  };

  const resetFilters = () => {
    setDashboardData((prev) => ({
      ...prev,
      filters: {},
    }));
  };

  return (
    <DashboardContext.Provider
      value={{
        data: dashboardData,
        isLoading,
        setDateRange,
        setActiveDataset,
        addDataset,
        removeDataset,
        setFilter,
        resetFilters,
        hasData: dashboardData.datasets.length > 0,
      }}
    >
      {children}
    </DashboardContext.Provider>
  );
};

export const useDashboard = (): DashboardContextType => {
  const context = useContext(DashboardContext);
  if (context === undefined) {
    throw new Error("useDashboard must be used within a DashboardProvider");
  }
  return context;
};