import React, { useState, useEffect } from 'react';
import { Sidebar } from '@/components/sidebar';
import { motion } from "framer-motion";
import StatCard from "@/components/dashboard/StatCard";
import { ChartCard } from "@/components/chart-card";
import {
  BarChart3,
  DollarSign,
  TrendingUp,
  ShoppingCart,
  Users,
  ArrowRight,
  ArrowUp,
  LineChart,
  Target,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart as RechartLineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  ComposedChart,
  ReferenceLine,
} from "recharts";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { toast } from "react-hot-toast";
import { PageHeader } from "@/components/page-header";
import type { DateRange } from "react-day-picker";
import channelROIData from "../../public/data/Channel_ROI_analyses.json";
import prepaidVsCodData from "../../public/data/prepaid_vs_cod.json";
import topPerformingChannelsData from "../../public/data/Top_performing_marketing_channels.json";
import salesVsNonSalesData from "../../public/data/sales_vs_non_sales_monthly.json";
import holidayData from "../../public/data/holiday_data.json";

// Add type definitions for the ROI data
interface ChannelROIData {
  monthly_roi: (number | string)[];
  average_roi: number;
}

interface ChannelROIChartData {
  channel: string;
  roi: number;
  monthlyROI: (number | string)[];
}

// Add type definitions for the payment data
interface PaymentData {
  order_payment_type: string;
  total_revenue: number;
  order_count: number;
  revenue_percentage: number;
}

interface MonthlyPaymentData {
  month: string;
  data: PaymentData[];
}

// Add type definitions for the top performing channels data
interface TopChannelData {
  channel: string;
  average_roi: number;
  attributed_revenue: string;
  revenue_percentage: string;
}

// Add type definition for sales data
interface SalesData {
  salesDaysAvgRevenue: number;
  nonSalesDaysAvgRevenue: number;
}

interface MonthlySalesData {
  [key: string]: SalesData;
}

// Add type definition for holiday data
interface HolidayData {
  Date: string;
  Revenue: number;
  orders: number;
  units: number;
  AOV: number;
  Holiday: string;
}

// Define interfaces for our data types
interface RevenueItem {
  month: string;
  revenue: number;
  marketingSpend: number;
  roi: string;
}

interface CategoryItem {
  category: string;
  revenue: number;
  units: number;
  growth: number;
  margin: number;
}

interface ChannelItem {
  channel: string;
  spend: number;
  revenue: number;
  roi: string;
  cac: number;
}

interface PromotionalItem {
  month: string;
  promotional: number;
  nonPromotional: number;
}

interface BudgetAllocationItem {
  channel: string;
  current: number;
  recommended: number;
}

interface KpiItem {
  period: string;
  target: number;
  actual: number;
}

interface CustomerJourneyItem {
  stage: string;
  conversion: number;
  dropoff: number;
}

interface ChangeData {
  value: number;
  positive: boolean;
}

interface DashboardKpiItem {
  title: string;
  value: string;
  change: ChangeData;
  icon: string;
  gradient: string;
}

interface DashboardData {
  revenueData: RevenueItem[];
  categoryData: CategoryItem[];
  channelData: ChannelItem[];
  promotionalData: PromotionalItem[];
  budgetAllocationData: BudgetAllocationItem[];
  kpiData: KpiItem[];
  customerJourneyData: CustomerJourneyItem[];
  dashboardKpiData: DashboardKpiItem[];
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

const pieColors = [
  "#38B2AC",
  "#4FD1C5",
  "#81E6D9",
  "#2D3748",
  "#4A5568",
  "#F6AD55",
  "#F6E05E",
  "#9AE6B4",
];

const ExecutiveSummary: React.FC = () => {
  // Add this if you want to use real data context (optional)
  // const { hasData, resetFilters } = useDashboard();

  // Or use local state for demo purposes
  const [hasData, setHasData] = useState(true);
  const resetFilters = () => {
    toast.success("Filters have been reset");
  };

  // Add state for dashboard data
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  // Campaign period filter — drives which slice of the underlying JSON metrics is shown below
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/data/dashboardData.json');
        const data = await response.json();
        setDashboardData(data['executive-summary']);
        setLoading(false);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Early return if data is loading
  if (loading || !dashboardData) {
    return (
      <div className="flex min-h-screen bg-background">
        <Sidebar />
        <div className="flex-1 p-8 ml-64 flex items-center justify-center">
          <p>Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  // Add page-specific filters
  const dashboardFilters = [
    {
      label: "Time Period",
      options: [
        { value: "yearly", label: "Yearly" },
        { value: "quarterly", label: "Quarterly" },
        { value: "monthly", label: "Monthly" },
      ],
      onChange: () => {},
      value: "yearly",
    },
    {
      label: "Region",
      options: [
        { value: "all", label: "All Regions" },
        { value: "north-america", label: "North America" },
        { value: "europe", label: "Europe" },
        { value: "asia", label: "Asia-Pacific" },
      ],
      onChange: () => {},
      value: "all",
    },
  ];

  // Use data from dashboardData
  const { revenueData, categoryData, channelData, promotionalData, budgetAllocationData, 
         customerJourneyData, kpiData, dashboardKpiData } = dashboardData;

  // Sort channelData by ROI
  const sortedChannelData = [...channelData].sort((a, b) => parseFloat(b.roi) - parseFloat(a.roi));
  
  const yearlyRevenue = revenueData.reduce((sum, item) => sum + item.revenue, 0);
  const yearlySpend = revenueData.reduce((sum, item) => sum + item.marketingSpend, 0);

  // Add icon mapping function
  const getIconComponent = (iconName: string) => {
    switch (iconName) {
      case 'dollar': return <DollarSign className="h-4 w-4" />;
      case 'trending-up': return <TrendingUp className="h-4 w-4" />;
      case 'bar-chart': return <BarChart3 className="h-4 w-4" />;
      case 'shopping-cart': return <ShoppingCart className="h-4 w-4" />;
      case 'users': return <Users className="h-4 w-4" />;
      case 'line-chart': return <LineChart className="h-4 w-4" />;
      case 'target': return <Target className="h-4 w-4" />;
      default: return <DollarSign className="h-4 w-4" />;
    }
  };

   // Transform channel ROI data for the chart
   const channelROIChartData: ChannelROIChartData[] = Object.entries(
    channelROIData as Record<string, ChannelROIData>
  ).map(([channel, data]) => ({
    channel,
    roi: data.average_roi,
    monthlyROI: data.monthly_roi,
  }));

  const sortedChannelROI = [...channelROIChartData].sort(
    (a, b) => b.roi - a.roi
  );

  // Transform payment data for the chart
  const paymentChartData = prepaidVsCodData.monthly_revenue_by_payment_type.map(
    (monthData) => {
      const codData = monthData.data.find(
        (d) => d.order_payment_type === "COD"
      );
      const prepaidData = monthData.data.find(
        (d) => d.order_payment_type === "Prepaid"
      );

      return {
        month: monthData.month,
        cod: codData ? codData.total_revenue : 0,
        prepaid: prepaidData ? prepaidData.total_revenue : 0,
        total:
          (codData ? codData.total_revenue : 0) +
          (prepaidData ? prepaidData.total_revenue : 0),
      };
    }
  );

  // Transform top performing channels data
  const topChannels =
    topPerformingChannelsData.top_performing_marketing_channels.current_month;

  // Transform sales data for the chart
  const salesChartData = Object.entries(
    salesVsNonSalesData.monthlyAverageRevenue
  )
    .map(([month, data]) => {
      const [year, monthNum] = month.split("-");
      const date = new Date(parseInt(year), parseInt(monthNum) - 1);
      const monthName = date.toLocaleString("default", { month: "short" });
      return {
        month: `${monthName} ${year}`,
        sales: data.salesDaysAvgRevenue,
        nonSales: data.nonSalesDaysAvgRevenue,
      };
    })
    .sort((a, b) => {
      const [monthA, yearA] = a.month.split(" ");
      const [monthB, yearB] = b.month.split(" ");
      const months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
      ];
      const monthIndexA = months.indexOf(monthA);
      const monthIndexB = months.indexOf(monthB);
      if (yearA !== yearB) return yearA.localeCompare(yearB);
      return monthIndexA - monthIndexB;
    });

  // Transform holiday data for the chart, restricted to the selected campaign period
  const holidayChartData = holidayData.holiday_data
    .filter((item) => {
      if (!dateRange?.from) return true;
      const date = new Date(item.Date);
      if (date < dateRange.from) return false;
      if (dateRange.to && date > dateRange.to) return false;
      return true;
    })
    .sort((a, b) => b.Revenue - a.Revenue)
    .map((item) => ({
      holiday: item.Holiday,
      sales: item.Revenue,
      orders: item.orders,
      aov: item.AOV,
    }));

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 p-8 ml-64">
        <motion.div
          className="space-y-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <PageHeader
            title="Executive Summary"
            subtitle="Overview of key marketing performance metrics and strategic insights"
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
            onResetFilters={() => setDateRange(undefined)}
            filters={[
              {
                label: "Time Period",
                options: [
                  { value: "yearly", label: "Yearly" },
                  { value: "quarterly", label: "Quarterly" },
                  { value: "monthly", label: "Monthly" },
                ],
                onChange: () => {},
                value: "yearly",
              },
            ]}
          />
          
          <motion.div variants={item} className="col-span-5 grid grid-cols-5 gap-1 mb-6">
            {dashboardKpiData.map((kpi, i) => (
              <StatCard
                key={i}
                title={kpi.title}
                value={kpi.value}
                change={null}
                icon={getIconComponent(kpi.icon || 'dollar')}
                bgGradient={kpi.gradient}
                delay={i}
              />
            ))}
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <ChartCard
              title="Holiday Sales Performance"
              height={320}
              tooltip={
                dateRange?.from
                  ? `Showing ${holidayChartData.length} holiday(s) between ${dateRange.from.toLocaleDateString()} and ${(dateRange.to ?? dateRange.from).toLocaleDateString()}`
                  : `Showing all ${holidayChartData.length} recorded holidays`
              }
            >
              {holidayChartData.length === 0 ? (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  No holidays fall within the selected date range.
                </div>
              ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={holidayChartData} layout="vertical">
                  <CartesianGrid
                    strokeDasharray="3 3"
                    horizontal={true}
                    vertical={false}
                  />
                  <XAxis
                    type="number"
                    tickFormatter={(value) =>
                      `₹${(value / 10000000).toFixed(1)}Cr`
                    }
                    domain={[0, "dataMax + 10000000"]}
                  />
                  <YAxis
                    dataKey="holiday"
                    type="category"
                    width={120}
                    tick={{ fontSize: 12 }}
                    interval={0}
                  />
                  <Tooltip
                    formatter={(value) =>
                      `₹${(Number(value) / 10000000).toFixed(2)}Cr`
                    }
                    labelFormatter={(label) => `Holiday: ${label}`}
                  />
                  <Bar
                    dataKey="sales"
                    name="Sales"
                    fill="#38B2AC"
                    barSize={20}
                    label={{
                      position: "right",
                      formatter: (value) =>
                        `₹${(Number(value) / 10000000).toFixed(1)}Cr`,
                    }}
                  />
                </BarChart>
              </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard title="Channel ROI Analysis" height={320}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sortedChannelROI}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="channel"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    interval={0}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    domain={[-1, 1.5]}
                    tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                    label={{
                      value: "ROI (%)",
                      angle: -90,
                      position: "insideLeft",
                      style: { textAnchor: "middle" },
                    }}
                  />
                  <Tooltip
                    formatter={(value: number) => [
                      `${(value * 100).toFixed(1)}%`,
                      "ROI",
                    ]}
                    labelFormatter={(label) => `Channel: ${label}`}
                  />
                  <ReferenceLine
                    y={0}
                    stroke="#666"
                    strokeDasharray="3 3"
                    strokeWidth={2}
                  />
                  <Bar dataKey="roi" fill="#4FD1C5" name="ROI">
                    {sortedChannelROI.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.roi >= 0 ? "#4FD1C5" : "#F56565"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="col-span-1">
              <ChartCard title="Revenue By Product Category" height={400}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={true}
                      label={({ name, percent }) =>
                        `${name} ${(percent * 100).toFixed(0)}%`
                      }
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="revenue"
                      nameKey="category"
                      paddingAngle={0}
                    >
                      {categoryData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={pieColors[index % pieColors.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) =>
                        `₹${(Number(value) / 10000000).toFixed(2)}Cr`
                      }
                      labelFormatter={(label) => `Category: ${label}`}
                      contentStyle={{
                        backgroundColor: "rgba(255, 255, 255, 0.95)",
                        border: "1px solid #E2E8F0",
                        borderRadius: "4px",
                        fontSize: "12px",
                        padding: "8px",
                      }}
                      wrapperStyle={{ outline: "none" }}
                    />
                    <Legend
                      verticalAlign="bottom"
                      height={36}
                      wrapperStyle={{ fontSize: "12px" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            <div className="col-span-2">
              <ChartCard
                title="Monthly Sales vs Non-Sales Revenue"
                height={400}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={salesChartData}
                    layout="vertical"
                    margin={{ top: 10, right: 10, left: 10, bottom: 10 }}
                  >
                    <XAxis
                      type="number"
                      tickFormatter={(value) =>
                        `₹${(value / 10000000).toFixed(1)}Cr`
                      }
                      domain={[0, "dataMax + 10000000"]}
                      height={40}
                      tick={{ fontSize: 11 }}
                      padding={{ left: 0, right: 0 }}
                    />
                    <YAxis
                      type="category"
                      dataKey="month"
                      width={100}
                      tick={{ fontSize: 11 }}
                      interval={0}
                      padding={{ top: 0, bottom: 0 }}
                    />
                    <CartesianGrid
                      strokeDasharray="3 3"
                      horizontal={true}
                      vertical={false}
                      stroke="#E2E8F0"
                    />
                    <Tooltip
                      formatter={(value) =>
                        `₹${(Number(value) / 10000000).toFixed(2)}Cr`
                      }
                      labelFormatter={(label) => `Month: ${label}`}
                      contentStyle={{
                        backgroundColor: "rgba(255, 255, 255, 0.95)",
                        border: "1px solid #E2E8F0",
                        borderRadius: "4px",
                        fontSize: "12px",
                      }}
                    />
                    <Legend
                      verticalAlign="top"
                      height={30}
                      wrapperStyle={{ fontSize: "12px" }}
                    />
                    <Bar
                      dataKey="sales"
                      name="Sales Days Revenue"
                      fill="#38B2AC"
                      barSize={16}
                      radius={[0, 4, 4, 0]}
                    />
                    <Bar
                      dataKey="nonSales"
                      name="Non-Sales Days Revenue"
                      fill="#F6AD55"
                      barSize={16}
                      radius={[0, 4, 4, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <ChartCard title="Monthly Revenue & Marketing Spend" height={280}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" />
                  <YAxis 
                    yAxisId="left" 
                    orientation="left" 
                    tickFormatter={(value) => `₹${(value / 1_000_000).toFixed(0)}M`} 
                    domain={[0, 550_000_000]}
                  />
                  <YAxis 
                    yAxisId="right" 
                    orientation="right" 
                    tickFormatter={(value) => `₹${(value / 1_000_000_000).toFixed(1)}B`} 
                    domain={[0, 1_800_000_000]}
                  />
                  <Tooltip 
                    formatter={(value) => [`₹${Number(value).toLocaleString()}`, value === revenueData[0].revenue ? "Revenue" : "Marketing Spend"]}
                    labelFormatter={(label) => `Month: ${label}`}
                  />
                  <Legend />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="revenue"
                    name="Revenue"
                    fill="#38B2AC"
                    fillOpacity={0.3}
                    stroke="#38B2AC"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="marketingSpend"
                    name="Marketing Spend"
                    stroke="#F6AD55"
                    strokeWidth={2}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Prepaid vs COD Revenue" height={280}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={paymentChartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="month"
                    tickFormatter={(value) =>
                      value.split("-").slice(1).join("-")
                    }
                    interval={0}
                  />
                  <YAxis
                    tickFormatter={(value) =>
                      `₹${(value / 10000000).toFixed(1)}Cr`
                    }
                    domain={[0, "dataMax + 10000000"]}
                  />
                  <Tooltip
                    formatter={(value) => `₹${Number(value).toLocaleString()}`}
                    labelFormatter={(label) => `Month: ${label}`}
                  />
                  <Legend />
                  <Bar
                    dataKey="cod"
                    name="COD Revenue"
                    fill="#38B2AC"
                    stackId="a"
                    barSize={20}
                  />
                  <Bar
                    dataKey="prepaid"
                    name="Prepaid Revenue"
                    fill="#81E6D9"
                    stackId="a"
                    barSize={20}
                  />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <div className="mb-6">
            <ChartCard title="Top Performing Marketing Channels" height="auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Channel</TableHead>
                    <TableHead className="text-right">
                      Attributed Revenue
                    </TableHead>
                    <TableHead className="text-right">Revenue %</TableHead>
                    <TableHead className="text-right">ROI</TableHead>
                    <TableHead className="text-right">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topChannels.map((channel, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">
                        {channel.channel}
                      </TableCell>
                      <TableCell className="text-right">
                        ₹
                        {channel.attributed_revenue
                          .replace("$", "")
                          .replace(",", "")}
                      </TableCell>
                      <TableCell className="text-right">
                        {channel.revenue_percentage}
                      </TableCell>
                      <TableCell
                        className={cn(
                          "text-right font-medium",
                          channel.average_roi >= 0.5
                            ? "text-green-500"
                            : channel.average_roi >= 0
                            ? "text-amber-500"
                            : "text-red-500"
                        )}
                      >
                        {(channel.average_roi * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell className="text-right">
                        <span
                          className={cn(
                            "px-2 py-1 rounded-full text-xs",
                            channel.average_roi >= 0.5
                              ? "bg-green-100 text-green-800"
                              : channel.average_roi >= 0
                              ? "bg-amber-100 text-amber-800"
                              : "bg-red-100 text-red-800"
                          )}
                        >
                          {channel.average_roi >= 0.5
                            ? "Excellent"
                            : channel.average_roi >= 0
                            ? "Good"
                            : "Needs Improvement"}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ChartCard>
          </div>

          <div className="bg-card p-6 rounded-lg border shadow mb-6">
            <h3 className="text-lg font-medium mb-4 flex items-center">
              <ArrowRight className="mr-2 h-5 w-5 text-marketing-primary" />
              Strategic Recommendations
            </h3>

            <div className="space-y-4">
              <div className="flex items-start gap-2">
                <ArrowUp className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <p className="font-medium">
                    Adjust Investment in Marketing Channels
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Reduce investment in Sponsorship and increase the investment in Affiliates and Content Marketing as per the analysis from the ROI Models.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <ArrowUp className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <p className="font-medium">Invest in Key Product Categories</p>
                  <p className="text-sm text-muted-foreground">
                    Invest in DSLR, Gaming Console, Gaming Mouse Pad, and Cooling Pad as they are important proportional products for the revenue.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <ArrowUp className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <p className="font-medium">Seasonal Sales Strategy</p>
                  <p className="text-sm text-muted-foreground">
                    Keep 10 and 8 days sale in December and March respectively as per seasonality analysis to maximize revenue.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default ExecutiveSummary;
