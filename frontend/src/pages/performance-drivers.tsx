import React, { useState } from "react";
import type { DateRange } from "react-day-picker";
import { isMonthLabelInRange } from "@/lib/date-labels";
import { Sidebar } from "@/components/sidebar";
import { Footer } from "@/components/footer";
import { PageHeader } from "@/components/page-header";
import { ChartCard } from "@/components/chart-card";
import { motion } from "framer-motion";
import StatCard from "@/components/dashboard/StatCard";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
  Treemap,
  ReferenceLine,
  ComposedChart,
  LabelList,
} from "recharts";
import {
  DollarSign,
  Users,
  CreditCard,
  ShoppingBag,
  Calendar,
  HeartPulse,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import dashboardData from "../../public/data/dashboardData.json";
import correlationData from "../../public/data/correlation_with_revenue.json";
import holidayData from "../../public/data/holiday_data.json";

// Add type definition for correlation data
interface CorrelationData {
  factor: string;
  correlation: number;
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

const PerformanceDrivers = () => {
  const {
    npsData,
    paymentTypeData,
    productCategoryData,
    treemapData,
    kpiData,
    productComparisonData
  } = dashboardData["performance-drivers"];

  // Transform correlation data for the chart
  const correlationChartData =
    correlationData.correlations_with_revenue_gmv.sort(
      (a, b) => Math.abs(b.correlation) - Math.abs(a.correlation)
    );

  // Campaign period filter — restricts the NPS trend and holiday table to the selected range
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);
  const filteredNpsData = npsData.filter((row: { month: string }) =>
    isMonthLabelInRange(row.month, dateRange?.from, dateRange?.to)
  );

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

  // Transform KPI data for the chart
  const kpiChartData = [
    { period: "Q1", target: 2500000, actual: 2350000 },
    { period: "Q2", target: 2750000, actual: 2950000 },
    { period: "Q3", target: 3000000, actual: 3200000 },
    { period: "Q4", target: 3500000, actual: 3350000 },
  ];

  const filters = [
    {
      label: "Year",
      options: [
        { value: "2023", label: "2023" },
        { value: "2022", label: "2022" },
        { value: "2021", label: "2021" },
      ],
      onChange: () => {},
      value: "2023",
    },
    {
      label: "Category",
      options: [
        { value: "all", label: "All Categories" },
        { value: "smartphones", label: "Smartphones" },
        { value: "laptops", label: "Laptops" },
        { value: "televisions", label: "Televisions" },
      ],
      onChange: () => {},
      value: "all",
    },
    {
      label: "Customer Segment",
      options: [
        { value: "all", label: "All Segments" },
        { value: "new", label: "New Customers" },
        { value: "returning", label: "Returning Customers" },
        { value: "loyal", label: "Loyal Customers" },
      ],
      onChange: () => {},
      value: "all",
    },
  ];

  const positiveColor = "#38B2AC";
  const negativeColor = "#FC8181";
  const COLORS = [
    "#38B2AC",
    "#4FD1C5",
    "#71d941",
    "#2D3748",

    "#2053d4",
    "#9AE6B4",
  ];

  const kpiCards = [
    {
      title: "Active Customers",
      value: kpiData.activeCustomers.value,
      change: kpiData.activeCustomers.change,
      icon: <Users className="h-4 w-4" />,
      gradient:
        "linear-gradient(90deg, rgb(59, 130, 246) 0%, rgb(37, 99, 235) 100%)",
    },
    {
      title: "Avg. NPS Score",
      value: kpiData.avgNPS.value,
      change: kpiData.avgNPS.change,
      icon: <HeartPulse className="h-4 w-4" />,
      gradient:
        "linear-gradient(90deg, rgb(239, 68, 68) 0%, rgb(220, 38, 38) 100%)",
    },
    {
      title: "Total Customers",
      value: kpiData.totalCustomers.value.toLocaleString(),
      change: kpiData.totalCustomers.change,
      icon: <Users className="h-4 w-4" />,
      gradient:
        "linear-gradient(90deg, rgb(99, 102, 241) 0%, rgb(79, 70, 229) 100%)",
    },
    {
      title: "Repeat Purchase",
      value: `${kpiData.repeatRate.value}%`,
      change: kpiData.repeatRate.change,
      icon: <ShoppingBag className="h-4 w-4" />,
      gradient:
        "linear-gradient(90deg, rgb(245, 158, 11) 0%, rgb(217, 119, 6) 100%)",
    },
  ];

  // Animation variants
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  const formatCurrency = (value: number) => {
    return `₹${value.toLocaleString()}`;
  };

  const formatTooltipValue = (value: number) => {
    return `₹${value.toLocaleString()}`;
  };
  const formatPercentage = (value: number) => `${value.toFixed(1)}%`;
  

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex">
        <Sidebar />

        <main className="flex-1 p-6 overflow-y-auto ml-64">
          <PageHeader
            title="Performance Drivers"
            subtitle="Identifying key factors influencing marketing performance"
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
            onResetFilters={() => setDateRange(undefined)}
            filters={filters}
          />

          {/* Animated Stats Cards */}
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 mb-4"
          >
            {kpiCards.map((kpi, i) => (
              <motion.div key={i} variants={item}>
                <StatCard
                  title={kpi.title}
                  value={kpi.value}
                  change={kpi.change}
                  icon={kpi.icon}
                  delay={i}
                  bgGradient={kpi.gradient}
                />
              </motion.div>
            ))}
          </motion.div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <ChartCard
              title="NPS Score vs. Revenue"
              tooltip="Relationship between customer satisfaction and revenue"
              height={300}
            >
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={filteredNpsData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" orientation="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="nps"
                    name="NPS Score"
                    stroke="#8884d8"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="revenue"
                    name="Revenue"
                    stroke="#82ca9d"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard
              title="Payment Type Analysis"
              tooltip="Comparison of payment methods: COD vs Prepaid"
              height={300}
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={paymentTypeData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" />
                  <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                  <YAxis yAxisId="right" orientation="right" stroke="#fcba03" />
                  <Tooltip />
                  <Legend />
                  <Bar
                    yAxisId="left"
                    dataKey="Order Percentace"
                    name="Order %"
                    fill="#8884d8"
                  />
                  <Bar
                    yAxisId="left"
                    dataKey="GMV Percentage"
                    name="GMV %"
                    fill="#82ca9d"
                  />
                  <Bar
                    yAxisId="right"
                    dataKey="Average Order Value"
                    name="Avg Order Value"
                    fill="#ffc658"
                  />
                  {/* <Bar
                    yAxisId="left"
                    dataKey="Avg Units per Order"
                    name="Avg Units per Order"
                    fill="#ff8042"
                  /> */}
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          {/* Product Comparison Chart - Order vs GMV Percentage */}
          <ChartCard
            title="Product Category Performance"
            tooltip="Comparison of order volume and GMV percentage"
            height={350}
          >
            <ResponsiveContainer width="100%" height={350}>
              <BarChart
                data={productComparisonData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis yAxisId="left" orientation="left" label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value, name) => {
                  if (name === "orderPercentage" || name === "gmvPercentage") return [`${value}%`, name === "orderPercentage" ? "Order %" : "GMV %"];
                  return [value, name];
                }} />
                <Legend />
                <Bar yAxisId="left" dataKey="orderPercentage" name="Order %" fill="#8884d8" radius={[4, 4, 0, 0]}>
                  <LabelList dataKey="orderPercentage" position="top" formatter={formatPercentage} />
                </Bar>
                <Bar yAxisId="left" dataKey="gmvPercentage" name="GMV %" fill="#82ca9d" radius={[4, 4, 0, 0]}>
                  <LabelList dataKey="gmvPercentage" position="top" formatter={formatPercentage} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

            <ChartCard
              title="Product Category & Subcategory Revenue"
              tooltip="Hierarchical view of revenue by product category"
              height={320}
            >
              <ResponsiveContainer width="100%" height="100%">
                <Treemap
                  data={treemapData}
                  dataKey="size"
                  aspectRatio={4 / 3}
                  stroke="#fff"
                  nameKey="name"
                >
                  <Tooltip
                    formatter={(value) =>
                      `₹${(Number(value) / 1000000).toFixed(2)}M`
                    }
                  />
                </Treemap>
              </ResponsiveContainer>
            </ChartCard>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <ChartCard
              title="Key Revenue Drivers Correlation"
              tooltip="Correlation coefficient of factors with revenue (higher is stronger)"
              height={400}
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={correlationChartData}
                  layout="vertical"
                  margin={{ top: 20, right: 20, left: 2, bottom: 2 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    horizontal={true}
                    vertical={false}
                  />
                  <XAxis
                    type="number"
                    domain={[-1, 1]}
                    tickFormatter={(value) =>
                      typeof value === "number" ? value.toFixed(2) : value
                    }
                    height={50}
                    tick={{ fontSize: 12 }}
                    padding={{ left: 0, right: 0 }}
                  />
                  <YAxis
                    dataKey="factor"
                    type="category"
                    width={140}
                    tick={{ fontSize: 12 }}
                    interval={0}
                    padding={{ top: 0, bottom: 0 }}
                  />
                  <Tooltip
                    formatter={(value) =>
                      typeof value === "number" ? value.toFixed(3) : value
                    }
                    labelFormatter={(label) => `Factor: ${label}`}
                  />
                  <ReferenceLine x={0} stroke="#666" strokeWidth={2} />
                  <Bar
                    dataKey="correlation"
                    name="Correlation with Revenue"
                    barSize={20}
                  >
                    {correlationChartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          entry.correlation >= 0 ? positiveColor : negativeColor
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard
              title="Discount vs Order Count"
              tooltip="Relationship between discount percentage and order count by category"
              height={400}
            >
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart
                  margin={{ top: 20, right: 20, bottom: 20, left: 40 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    dataKey="discount"
                    name="Discount (%)"
                    domain={[30, 50]}
                    label={{
                      value: "Discount (%)",
                      position: "insideBottom",
                      offset: -4,
                    }}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <YAxis
                    type="number"
                    dataKey="orders"
                    name="Order Count"
                    domain={[0, 1000000]}
                    tickFormatter={(value) => value.toLocaleString()}
                    label={{
                      value: "Order Count",
                      angle: -90,
                      position: "insideLeft",
                      offset: -20,
                    }}
                  />
                  <Tooltip
                    formatter={(value, name) => {
                      if (name === "Discount (%)")
                        return [`${Number(value).toFixed(2)}%`, name];
                      if (name === "Order Count")
                        return [value.toLocaleString(), name];
                      return [value, name];
                    }}
                    labelFormatter={(value) => {
                      const item = [
                        {
                          category: "Camera Accessory",
                          discount: 48.19,
                          orders: 257493,
                        },
                        {
                          category: "Entertainment Small",
                          discount: 43.77,
                          orders: 944698,
                        },
                        {
                          category: "Gaming Hardware",
                          discount: 42.44,
                          orders: 230958,
                        },
                        { category: "Camera", discount: 31.21, orders: 101172 },
                        {
                          category: "Game CD/DVD",
                          discount: 30.94,
                          orders: 114503,
                        },
                      ].find((item) => Math.abs(item.discount - value) < 0.01);
                      return item ? item.category : "";
                    }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white p-3 border border-gray-200 rounded shadow-sm">
                            <p className="font-bold text-sm mb-1">
                              {data.category}
                            </p>
                            <p className="text-xs">
                              <span className="font-medium">Discount:</span>{" "}
                              {data.discount.toFixed(2)}%
                            </p>
                            <p className="text-xs">
                              <span className="font-medium">Orders:</span>{" "}
                              {data.orders.toLocaleString()}
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend />
                  <Scatter
                    data={[
                      {
                        category: "Camera Accessory",
                        discount: 48.19,
                        orders: 257493,
                      },
                      {
                        category: "Entertainment Small",
                        discount: 43.77,
                        orders: 944698,
                      },
                      {
                        category: "Gaming Hardware",
                        discount: 42.44,
                        orders: 230958,
                      },
                      { category: "Camera", discount: 31.21, orders: 101172 },
                      {
                        category: "Game CD/DVD",
                        discount: 30.94,
                        orders: 114503,
                      },
                    ]}
                    fill="#ffffff"
                  >
                    {[
                      {
                        category: "Camera Accessory",
                        discount: 48.19,
                        orders: 257493,
                      },
                      {
                        category: "Entertainment Small",
                        discount: 43.77,
                        orders: 944698,
                      },
                      {
                        category: "Gaming Hardware",
                        discount: 42.44,
                        orders: 230958,
                      },
                      { category: "Camera", discount: 31.21, orders: 101172 },
                      {
                        category: "Game CD/DVD",
                        discount: 30.94,
                        orders: 114503,
                      },
                    ].map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Scatter>

                  <ReferenceLine x={0} y={0} stroke="#666" />
                </ScatterChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <div className="mb-6">
            <ChartCard
              title="Holiday Sales Analysis"
              tooltip="Detailed performance metrics for key holiday sales periods"
              height="auto"
            >
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Holiday</TableHead>
                    <TableHead className="text-right">Sales Revenue</TableHead>
                    <TableHead className="text-right">Orders</TableHead>
                    <TableHead className="text-right">AOV</TableHead>
                    <TableHead className="text-right">Performance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {holidayChartData.map((item, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">
                        {item.holiday}
                      </TableCell>
                      <TableCell className="text-right">
                        ₹{(item.sales / 10000000).toFixed(2)}Cr
                      </TableCell>
                      <TableCell className="text-right">
                        {item.orders.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        ₹{item.aov.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <span
                          className={cn(
                            "px-2 py-1 rounded-full text-xs",
                            item.sales >= 11000000
                              ? "bg-green-100 text-green-800"
                              : item.sales >= 10000000
                              ? "bg-amber-100 text-amber-800"
                              : "bg-red-100 text-red-800"
                          )}
                        >
                          {item.sales >= 11000000
                            ? "Strong"
                            : item.sales >= 10000000
                            ? "Moderate"
                            : "Weak"}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ChartCard>
          </div>
        </main>
      </div>
    </div>
  );
};

export default PerformanceDrivers;
