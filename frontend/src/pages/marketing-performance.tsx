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
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
  PieChart,
  Pie,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import { DollarSign, TrendingUp, BarChart3, ShoppingCart, ZapIcon, Target, Award, Layers, Users, Clock, CreditCard, TrendingDown } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { cn } from '@/lib/utils';
import dashboardData from '../../public/data/dashboardData.json';

const MarketingPerformance = () => {
  // Get data from dashboardData.json
  const {
    monthlyRevenueData,
    categoryRevenueData,
    channelData,
    performanceRadarData,
    kpiData,
    additionalKPIData // Add this to get the additional KPI data
  } = dashboardData['marketing-performance'];
  
  // Colors for charts
  const COLORS = ['#38B2AC', '#4FD1C5', '#81E6D9', '#2D3748', '#4A5568', '#F6AD55', '#F6E05E', '#9AE6B4'];

  // Campaign period filter — restricts Monthly Revenue Trends to the selected range
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);
  const filteredMonthlyRevenueData = monthlyRevenueData.filter((row: { month: string }) =>
    isMonthLabelInRange(row.month, dateRange?.from, dateRange?.to)
  );

  // For demo filters
  const filters = [
    {
      label: "Time Period",
      options: [
        { value: "monthly", label: "Monthly" },
        { value: "quarterly", label: "Quarterly" },
        { value: "yearly", label: "Yearly" },
      ],
      onChange: () => {},
      value: "monthly",
    },
    {
      label: "Channel",
      options: [
        { value: "all", label: "All Channels" },
        { value: "paid-search", label: "Paid Search" },
        { value: "social", label: "Social Media" },
        { value: "email", label: "Email" },
        { value: "display", label: "Display" },
      ],
      onChange: () => {},
      value: "all",
    },
    {
      label: "Category",
      options: [
        { value: 'all', label: 'All Categories' },
        { value: 'cameras', label: 'Cameras' },
        { value: 'entertainment', label: 'Entertainment' },
        { value: 'gaming', label: 'Gaming' },
      ],
      onChange: () => {},
      value: "all",
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

  // Add the additional KPI cards configuration
  const additionalKpiCards = [
    {
      title: "Total GMV",
      value: additionalKPIData?.totalGMV?.value || "₹24.5M",
      change: additionalKPIData?.totalGMV?.change || { positive: true, value: 12.3 },
      icon: <ShoppingCart className="h-4 w-4" />,
      gradient: "linear-gradient(135deg, #059669 0%, #34D399 100%)",
      className: "border-l-4 border-emerald-500",
    },
    {
      title: "Customer LTV",
      value: additionalKPIData?.clv?.value || "₹4,250",
      change: additionalKPIData?.clv?.change || { positive: true, value: 8.7 },
      icon: <Users className="h-4 w-4" />,
      gradient: "linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)",
      className: "border-r-4 border-violet-500",
    },
    {
      title: "Average SLA",
      value: additionalKPIData?.avgSLA?.value || "4.2 days",
      change: additionalKPIData?.avgSLA?.change || { positive: false, value: 1.5 },
      icon: <Clock className="h-4 w-4" />,
      gradient: "linear-gradient(135deg, #DB2777 0%, #F472B6 100%)",
      className: "border-t-4 border-pink-500",
    },
    {
      title: "ARPPU",
      value: additionalKPIData?.arppu?.value || "₹1,850",
      change: additionalKPIData?.arppu?.change || { positive: true, value: 5.2 },
      icon: <CreditCard className="h-4 w-4" />,
      gradient: "linear-gradient(135deg, #2563EB 0%, #60A5FA 100%)",
      className: "border-b-4 border-blue-500",
    },
    {
      title: "GMROI",
      value: additionalKPIData?.gmroi?.value || "3.8x",
      change: additionalKPIData?.gmroi?.change || { positive: true, value: 2.1 },
      icon: <TrendingDown className="h-4 w-4" />,
      gradient: "linear-gradient(135deg, #DC2626 0%, #F87171 100%)",
      className: "shadow-lg ring-2 ring-red-500",
    },
  ];

  // Get icon component based on string name
  const getIconComponent = (iconName: string) => {
    switch (iconName) {
      case 'dollar': return <DollarSign className="h-4 w-4" />;
      case 'trending-up': return <TrendingUp className="h-4 w-4" />;
      case 'bar-chart': return <BarChart3 className="h-4 w-4" />;
      case 'shopping-cart': return <ShoppingCart className="h-4 w-4" />;
      case 'target': return <Target className="h-4 w-4" />;
      case 'award': return <Award className="h-4 w-4" />;
      case 'layers': return <Layers className="h-4 w-4" />;
      default: return <DollarSign className="h-4 w-4" />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex">
        <Sidebar />

        <main className="flex-1 p-6 overflow-y-auto ml-64">
          <PageHeader
            title="Marketing Performance"
            subtitle="Analysis of revenue trends and marketing channel effectiveness"
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
            onResetFilters={() => setDateRange(undefined)}
            filters={filters}
          />

          {/* Stats Row - Animated with Framer Motion */}  
          
          {/* Additional KPI Cards with Different Designs */}
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6"
          >
            {additionalKpiCards.map((kpi, i) => (
              <motion.div key={i} variants={item}>
                <div
                  className={`p-4 rounded-lg bg-white dark:bg-gray-800 ${kpi.className}`}
                  style={{
                    background: kpi.gradient,
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">
                      {kpi.title}
                    </span>
                    <div className="p-2 rounded-full bg-white/20">{kpi.icon}</div>
                  </div>
                  <div className="text-2xl font-bold text-white mb-1">
                    {kpi.value}
                  </div>
                  <div
                    className={`text-sm ${
                      kpi.change.positive ? "text-green-100" : "text-red-100"
                    }`}
                  >
                    {kpi.change.positive ? "↑" : "↓"} {kpi.change.value}%
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
          
          {/* First row of charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <ChartCard
              title="Monthly Revenue Trends"
              tooltip="Shows revenue performance against targets and marketing spend"
              height={300}
            >
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={filteredMonthlyRevenueData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip
                    formatter={(value) =>
                      `$${(Number(value) / 1000000).toFixed(2)}M`
                    }
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    name="Revenue"
                    stroke="#38B2AC"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 8 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="marketingSpend"
                    name="Marketing Spend"
                    stroke="#F6AD55"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="target"
                    name="Target"
                    stroke="#9F7AEA"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard
              title="Revenue by Product Category"
              tooltip="Shows revenue distribution across product categories"
              height={300}
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={categoryRevenueData.slice(0, 6)}
                  layout="vertical"
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    horizontal={true}
                    vertical={false}
                  />
                  <XAxis type="number" />
                  <YAxis dataKey="category" type="category" width={100} />
                  <Tooltip
                    formatter={(value) =>
                      `$${(Number(value) / 1000000).toFixed(2)}M`
                    }
                  />
                  <Legend />
                  <Bar
                    dataKey="revenue"
                    name="Revenue"
                    fill="#38B2AC"
                    label={{
                      position: "right",
                      formatter: (value) =>
                        `$${(Number(value) / 1000000).toFixed(1)}M`,
                    }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Second row of charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <ChartCard
              title="Marketing Channel ROI"
              tooltip="Higher values indicate better return on marketing investment"
              height={300}
            >
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="spend"
                    name="Marketing Spend"
                    domain={["auto", "auto"]}
                    label={{
                      value: "Marketing Spend ($)",
                      position: "insideBottom",
                      offset: -5,
                    }}
                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                  />
                  <YAxis
                    dataKey="roi"
                    name="ROI"
                    label={{
                      value: "ROI (x)",
                      angle: -90,
                      position: "insideLeft",
                    }}
                  />
                  <Tooltip
                    formatter={(value, name) => {
                      if (name === "Marketing Spend")
                        return `$${(Number(value) / 1000).toFixed(0)}K`;
                      if (name === "ROI") return `${value}x`;
                      return value;
                    }}
                    labelFormatter={(value) => {
                      const item = channelData.find(
                        (item) => item.spend === value
                      );
                      return item ? item.channel : "";
                    }}
                  />
                  <Scatter name="Channel ROI" data={channelData} fill="#38B2AC">
                    {channelData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard
              title="Company vs World"
              tooltip="Comparison of company performance against world averages"
              height={300}
            >
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart
                  outerRadius={90}
                  data={[
                    {
                      subject: "Paid Advertising (PPC)",
                      company: 50,
                      world: 29,
                    },
                    {
                      subject: "Search Engine Optimization (SEO)",
                      company: 10,
                      world: 7,
                    },
                    { subject: "Content Marketing", company: 12, world: 25 },
                    {
                      subject: "Social Media Marketing",
                      company: 5,
                      world: 11,
                    },
                    {
                      subject: "Online Marketing (ACOS)",
                      company: 23,
                      world: 28,
                    },
                  ]}
                >
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis domain={[0, 50]} />
                  <Radar
                    name="Company"
                    dataKey="company"
                    stroke="#38B2AC"
                    fill="#38B2AC"
                    fillOpacity={0.5}
                  />
                  <Radar
                    name="World"
                    dataKey="world"
                    stroke="#F6AD55"
                    fill="#F6AD55"
                    fillOpacity={0.5}
                  />
                  <Legend />
                  <Tooltip formatter={(value) => `${value}%`} />
                </RadarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Third row of charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <ChartCard
              title="Category Growth"
              tooltip="Year-over-year growth percentage by category"
              height={280}
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryRevenueData.slice(0, 5)}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="category" />
                  <YAxis />
                  <Tooltip formatter={(value) => `${value}%`} />
                  <Bar dataKey="growth" name="YoY Growth" radius={[4, 4, 0, 0]}>
                    {categoryRevenueData.slice(0, 5).map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.growth >= 0 ? "#38B2AC" : "#FC8181"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard
              title="Marketing Spend by Channel"
              tooltip="Distribution of marketing budget across channels"
              height={280}
            >
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={channelData.slice(0, 5)}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="spend"
                    nameKey="channel"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {channelData.slice(0, 5).map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `₹${(Number(value)/10000000).toFixed(2)} Cr`} />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Fourth row - Table */}
          <div className="mb-6">
            <ChartCard
              title="Marketing Channel Performance"
              tooltip="Detailed performance metrics for each marketing channel"
              height="auto"
            >
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Channel</TableHead>
                    <TableHead className="text-right">Spend (Cr)</TableHead>
                    <TableHead className="text-right">Attributed Revenue</TableHead>
                    <TableHead className="text-right">ROI</TableHead>
                    <TableHead className="text-right">Marginal ROI</TableHead>
                    <TableHead className="text-right">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {channelData.slice(0, 9).map((item, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">{item.channel}</TableCell>
                      <TableCell className="text-right">₹{(item.spend/10000000).toFixed(2)} Cr</TableCell>
                      <TableCell className="text-right">₹{(item.attributed_revenue/1000000).toFixed(2)} M</TableCell>
                      <TableCell 
                        className={cn(
                          "text-right font-medium",
                          item.roi >= 0.5 ? "text-green-500" : 
                          item.roi >= 0 ? "text-amber-500" : "text-red-500"
                        )}
                      >
                        {Number(item.roi).toFixed(2)}
                      </TableCell>
                      <TableCell 
                        className={cn(
                          "text-right font-medium",
                          item.marginal_roi >= 0.5 ? "text-green-500" : 
                          item.marginal_roi >= 0 ? "text-amber-500" : "text-red-500"
                        )}
                      >
                        {(Number(item.marginal_roi) * 100).toFixed(2)}%
                      </TableCell>
                      <TableCell className="text-right">
                        <span
                          className={cn(
                            "px-2 py-1 rounded-full text-xs",
                            item.roi >= 0.5 ? "bg-green-100 text-green-800" : 
                            item.roi >= 0 ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"
                          )}
                        >
                          {item.roi >= 0.5 ? "Good" : 
                           item.roi >= 0 ? "Average" : "Poor"}
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

export default MarketingPerformance;
