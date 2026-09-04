
import { useDashboard, DataSet } from "@/contexts/DashboardContext";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const DatasetSelector = () => {
  const { data, setActiveDataset } = useDashboard();

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

  return (
    <Select
      value={data.activeDatasetId || undefined}
      onValueChange={setActiveDataset}
    >
      <SelectTrigger className="w-full md:w-[300px]">
        <SelectValue placeholder="Select dataset" />
      </SelectTrigger>
      <SelectContent>
        {data.datasets.length === 0 ? (
          <div className="py-2 px-2 text-sm text-muted-foreground">
            No datasets available
          </div>
        ) : (
          data.datasets.map((dataset: DataSet) => (
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
  );
};

export default DatasetSelector;
