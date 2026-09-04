import React, { useState } from "react";
import type { DateRange } from "react-day-picker";
import { isMonthLabelInRange } from "@/lib/date-labels";
import { Sidebar } from "@/components/sidebar";
import { PageHeader } from "@/components/page-header";
import { ChartCard } from "@/components/chart-card";
import { motion } from "framer-motion";
import StatCard from "@/components/dashboard/StatCard";
import {
  TrendingUp,
  DollarSign,
  BarChart3,
  PieChart,
  LineChart,
  ShoppingCart,
  Users,
  Clock,
  CreditCard,
  TrendingDown,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BarChart,
  Bar,
  LineChart as ReLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart as RePieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import dashboardData from '../../public/data/dashboardData.json';

const MarketingROI: React.FC = () => {
  // Import data from dashboardData.json
  const {
    channelROIData,
    roiTrendsData,
    spendRevenueData,
    roiBySegmentData,
    campaignROIData,
    kpiData,
    monthlyROIData // Added monthly ROI data
  } = dashboardData["marketing-roi"];

  // Campaign period filter — restricts the ROI trend/area charts to the selected range
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);
  const filteredRoiTrendsData = roiTrendsData.filter((row: { month: string }) =>
    isMonthLabelInRange(row.month, dateRange?.from, dateRange?.to)
  );
  const filteredMonthlyROIData = monthlyROIData.filter((row: { Month: string }) =>
    isMonthLabelInRange(row.Month, dateRange?.from, dateRange?.to)
  );

  // Convert channelROIData to combined format for the chart
  const channelROICombinedData = channelROIData.map(item => ({
    name: item.name,
    ROI: item.roi,
    Spend: item.spend / 10000000,  // Convert to crores for better display
  }));

  // Format campaignROIData for the chart - convert to millions for display
  const formattedCampaignData = campaignROIData.map(item => ({
    name: item.name,
    Revenue: item.revenue / 10000000, // Convert to crores
  }));

  // Calculate total revenue and spend for the year
  const yearlyRevenue = spendRevenueData.reduce((total, item) => total + item.revenue, 0);
  const yearlySpend = spendRevenueData.reduce((total, item) => total + item.spend, 0);
  
  // Custom formatters to safely handle different value types
  const formatROI = (value: any) => {
    if (typeof value === 'number') {
      return [`${value}x`, 'ROI'];
    }
    return [value.toString(), "ROI"];
  };

  const formatCurrency = (value: any) => {
    if (typeof value === 'number') {
      return [`₹${(value/1000).toFixed(1)}K`, ''];
    }
    return [value, ''];
  };

  const formatCrores = (value: any) => {
    if (typeof value === 'number') {
      return [`₹${value.toFixed(2)}Cr`, 'Revenue (Crores)'];
    }
    return [value, ''];
  };
  
  // Map icon string names to actual icon components
  const getIconComponent = (iconName: string) => {
    switch (iconName) {
      case 'TrendingUp': return <TrendingUp className="h-4 w-4" />;
      case 'DollarSign': return <DollarSign className="h-4 w-4" />;
      case 'BarChart3': return <BarChart3 className="h-4 w-4" />;
      case 'LineChart': return <LineChart className="h-4 w-4" />;
      case 'PieChart': return <PieChart className="h-4 w-4" />;
      default: return <BarChart3 className="h-4 w-4" />;
    }
  };
  
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

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 p-6 overflow-y-auto ml-64">
        <PageHeader
          title="Marketing ROI Analysis"
          subtitle="Channel performance, budget allocation, and ROI optimization"
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

        {/* Original Stats Cards */}
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 mb-4"
        >
          {kpiData.map((kpi, i) => (
            <motion.div key={i} variants={item}>
              <StatCard
                title={kpi.title}
                value={kpi.value.replace('$', '')}
                change={kpi.change ? { value: kpi.change.value } : null}
                icon={getIconComponent(kpi.icon || 'dollar')}
                delay={i}
                bgGradient={kpi.gradient}
              />
            </motion.div>
          ))}
        </motion.div>

        {/* AreaChart for Current Month ROI and Marginal ROI */}
        

        {/* AreaChart for Next Month ROI and Marginal ROI */}
        

        {/* Removed Additional KPI Cards section */}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <ChartCard
            title="Channel ROI Comparison"
            tooltip="Return on investment across different marketing channels"
            height={400}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={channelROICombinedData}
                margin={{ top: 20, right: 30, left: 20, bottom: 30 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={70}
                />
                <YAxis yAxisId="left" orientation="left" stroke="#8B5CF6" />
                <YAxis yAxisId="right" orientation="right" stroke="#D946EF" />
                <Tooltip formatter={(value, name) => {
                  if (name === 'ROI' && typeof value === 'number') return [`${value}x`, 'ROI'];
                  if (name === 'Spend' && typeof value === 'number') return [`₹${value.toFixed(2)}Cr`, 'Spend (Crores)'];
                  return [value, name];
                }} />
                <Legend />
                <Bar
                  yAxisId="left"
                  dataKey="ROI"
                  fill="#8B5CF6"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  yAxisId="right"
                  dataKey="Spend"
                  fill="#D946EF"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="ROI Trends by Channel"
            tooltip="How ROI is evolving over time for top channels"
            height={400}
          >
            <ResponsiveContainer width="100%" height="100%">
              <ReLineChart
                data={filteredRoiTrendsData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={formatROI} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="digital"
                  stroke="#F97316"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="sponsorship"
                  stroke="#0EA5E9"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="contentMarketing"
                  stroke="#D946EF"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="onlineMarketing"
                  stroke="#10B981"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="affiliates"
                  stroke="#EAB308"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="sem"
                  stroke="#8B5CF6"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
              </ReLineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard
          title="Current Month ROI and Marginal ROI"
          tooltip="Current month's average ROI and marginal ROI"
          height={400}
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={filteredMonthlyROIData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                <linearGradient id="colorCurrentROI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#F97316" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorCurrentMarginalROI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="Month" />
              <YAxis />
              <Tooltip formatter={(value, name) => {
                if (typeof value === 'number') {
                  return [`${value.toFixed(2)}`, name];
                }
                return [value, name];
              }} />
              <Legend />
              <Area
                type="monotone"
                dataKey="Current_Monthly_Avg_ROI"
                name="Current ROI"
                stroke="#F97316"
                fillOpacity={1}
                fill="url(#colorCurrentROI)"
              />
              <Area
                type="monotone"
                dataKey="Current_Month_Avg_Marginal_ROI"
                name="Current Marginal ROI"
                stroke="#10B981"
                fillOpacity={1}
                fill="url(#colorCurrentMarginalROI)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Next Month ROI and Marginal ROI"
          tooltip="Next month's projected average ROI and marginal ROI"
          height={400}
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={filteredMonthlyROIData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                <linearGradient id="colorNextROI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#D946EF" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#D946EF" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorNextMarginalROI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="Month" />
              <YAxis />
              <Tooltip formatter={(value, name) => {
                if (typeof value === 'number') {
                  return [`${value.toFixed(2)}`, name];
                }
                return [value, name];
              }} />
              <Legend />
              <Area
                type="monotone"
                dataKey="Next_Month_ROI"
                name="Next ROI"
                stroke="#D946EF"
                fillOpacity={1}
                fill="url(#colorNextROI)"
              />
              <Area
                type="monotone"
                dataKey="Next_Month_Avg_Marginal_ROI"
                name="Next Marginal ROI"
                stroke="#8B5CF6"
                fillOpacity={1}
                fill="url(#colorNextMarginalROI)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

          
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4 min-h-[450px]" >
          <ChartCard 
            title="Revenue by Discount Range" 
            tooltip="Revenue distribution across discount ranges"
            size="md"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={formattedCampaignData}
                margin={{ top: 20, right: 30, left: 80, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" />
                <Tooltip formatter={formatCrores} />
                <Bar dataKey="Revenue" fill="#8B5CF6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
          
          <ChartCard 
            title="Revenue by Discount Details" 
            tooltip="Detailed revenue metrics by discount range"
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Discount Range</TableHead>
                  <TableHead>Revenue (₹ Crore)</TableHead>
                  <TableHead>Performance</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {formattedCampaignData.map((campaign) => {
                  // Determine performance category based on revenue
                  const revenueCrores = campaign.Revenue;
                  let performanceCategory;
                  let colorClass;
                  
                  if (revenueCrores > 70) {
                    performanceCategory = 'Excellent';
                    colorClass = 'bg-green-100 text-green-800';
                  } else if (revenueCrores > 40) {
                    performanceCategory = 'Good';
                    colorClass = 'bg-blue-100 text-blue-800';
                  } else {
                    performanceCategory = 'Average';
                    colorClass = 'bg-yellow-100 text-yellow-800';
                  }
                  
                  return (
                    <TableRow key={campaign.name}>
                      <TableCell className="font-medium">{campaign.name}</TableCell>
                      <TableCell>₹{campaign.Revenue.toFixed(2)}Cr</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs ${colorClass}`}>
                          {performanceCategory}
                        </span>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </ChartCard>
        </div>
      </div>
    </div>
  );
};

export default MarketingROI;