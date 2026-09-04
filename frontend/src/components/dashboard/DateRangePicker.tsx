
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { useDashboard } from "@/contexts/DashboardContext";

interface DateRange {
  from: Date;
  to: Date;
}

const DateRangePicker = () => {
  const { data, setDateRange } = useDashboard();
  const [date, setDate] = useState<DateRange>({
    from: data.dateRange.start,
    to: data.dateRange.end,
  });
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (selectedDate: DateRange) => {
    setDate(selectedDate);
    if (selectedDate.from && selectedDate.to) {
      setDateRange(selectedDate.from, selectedDate.to);
      setIsOpen(false);
    }
  };

  const predefinedRanges = [
    { 
      label: "Last 30 days", 
      onClick: () => {
        const to = new Date();
        const from = new Date();
        from.setDate(from.getDate() - 30);
        handleSelect({ from, to });
      }
    },
    { 
      label: "Last quarter", 
      onClick: () => {
        const to = new Date();
        const from = new Date();
        from.setMonth(from.getMonth() - 3);
        handleSelect({ from, to });
      }
    },
    { 
      label: "Year to date", 
      onClick: () => {
        const to = new Date();
        const from = new Date(to.getFullYear(), 0, 1);
        handleSelect({ from, to });
      }
    },
    { 
      label: "Last year", 
      onClick: () => {
        const to = new Date();
        const from = new Date();
        from.setFullYear(from.getFullYear() - 1);
        handleSelect({ from, to });
      }
    },
  ];

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className="w-full justify-start text-left font-normal md:w-auto"
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {date.from ? (
            date.to ? (
              <>
                {format(date.from, "LLL dd, y")} -{" "}
                {format(date.to, "LLL dd, y")}
              </>
            ) : (
              format(date.from, "LLL dd, y")
            )
          ) : (
            <span>Pick a date range</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div className="flex flex-col sm:flex-row">
          <div className="border-r p-2 sm:p-3">
            <div className="space-y-2 sm:w-48">
              <h4 className="font-medium text-sm">Quick select</h4>
              {predefinedRanges.map((range) => (
                <Button 
                  key={range.label} 
                  variant="ghost" 
                  size="sm" 
                  className="w-full justify-start"
                  onClick={range.onClick}
                >
                  {range.label}
                </Button>
              ))}
            </div>
          </div>
          <Calendar
            initialFocus
            mode="range"
            defaultMonth={date.from}
            selected={date}
            onSelect={(range: any) => handleSelect(range || { from: undefined, to: undefined })}
            numberOfMonths={2}
            className="p-3"
          />
        </div>
      </PopoverContent>
    </Popover>
  );
};

export default DateRangePicker;
