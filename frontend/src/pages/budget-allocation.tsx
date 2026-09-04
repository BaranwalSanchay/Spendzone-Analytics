import React, { useState } from 'react';
import { Sidebar } from '@/components/sidebar';
import { PageHeader } from '@/components/page-header';
import { MarketingChart } from '@/components/marketing-chart';
import { motion } from "framer-motion";
import StatCard from '@/components/dashboard/StatCard';
import { ChartCard } from '@/components/chart-card';
import { DollarSign, LineChart, PieChart, TrendingUp, BarChart3 } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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
  PieChart as RePieChart,
  Pie,
  Cell,
  Treemap,
  Sankey,
  Scatter,
  ScatterChart,
  ZAxis
} from 'recharts';
import dashboardData from '../../public/data/dashboardData.json';
import robynSaturationData from '../../public/data/robyn_saturation.json';
import { SaturationCurves } from '@/components/dashboard/SaturationCurves';
import { WhatIfScenario } from '@/components/dashboard/WhatIfScenario';
import type { DateRange } from 'react-day-picker';
import { isMonthLabelInRange } from '@/lib/date-labels';

// Custom component for treemap cells
const CustomizedContent = (props: any) => {
  const { x, y, width, height, index, name, value } = props;
  const formatValue = (val: number) => `${val.toFixed(1)}%`;
  const formattedValue = typeof value === 'number' ? formatValue(value) : value;
  
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: props.colors && props.colors[index % props.colors.length] || '#8884d8',
          stroke: '#fff',
          strokeWidth: 2,
          strokeOpacity: 1,
        }}
      />
      {width > 50 && height > 25 ? (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - 8}
            textAnchor="middle"
            fill="#fff"
            fontSize={12}
            fontWeight="bold"
          >
            {name && name.split(': ')[1] || name}
          </text>
          <text
            x={x + width / 2}
            y={y + height / 2 + 10}
            textAnchor="middle"
            fill="#fff"
            fontSize={11}
          >
            {formattedValue}
          </text>
        </>
      ) : null}
    </g>
  );
};

const BudgetAllocation: React.FC = () => {
  // Import data from dashboardData.json
  const {
    channelAllocationData,
    quarterlyBudgetData,
    budgetVsROIData,
    budgetByRegionData,
    budgetTreemapData,
    kpiData,
    subCategoryImportanceData,
    quarterlyChannelAllocation,
    monthlyChannelAllocation // Add this new data import
  } = dashboardData["budget-allocation"];

  const transformQuarterlyChannelData = () => {
    if (!quarterlyChannelAllocation || !Array.isArray(quarterlyChannelAllocation)) {
      return [];
    }
    
    return quarterlyChannelAllocation.map(item => {
      return {
        quarter: item.quarter,
        TV: item.channels.TV,
        Digital: item.channels.Digital,
        Sponsorship: item.channels.Sponsorship,
        "Content Marketing": item.channels["Content Marketing"],
        "Online marketing": item.channels["Online marketing"],
        Affiliates: item.channels.Affiliates,
        SEM: item.channels.SEM
      };
    });
  };
  
  // Add this variable to store the transformed data
  const quarterlyChannelData = transformQuarterlyChannelData();

  const transformMonthlyChannelData = () => {
    if (!monthlyChannelAllocation || !Array.isArray(monthlyChannelAllocation)) {
      return [];
    }
    
    return monthlyChannelAllocation.map(item => {
      return {
        month: item.month,
        TV: item.channels.TV,
        Digital: item.channels.Digital,
        Sponsorship: item.channels.Sponsorship,
        "Content Marketing": item.channels["Content Marketing"],
        "Online marketing": item.channels["Online marketing"],
        Affiliates: item.channels.Affiliates,
        SEM: item.channels.SEM,
        investment: item.investment,
        projectedRevenue: item.projectedRevenue
      };
    });
  };
  
  // Add this variable to store the transformed data
  const monthlyChannelData = transformMonthlyChannelData();

  // Campaign period filter — restricts the monthly channel allocation chart to the selected range
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);
  const filteredMonthlyChannelData = monthlyChannelData.filter((row: { month: string }) =>
    isMonthLabelInRange(row.month, dateRange?.from, dateRange?.to)
  );

  // Flatten the treemap data for Recharts
  const flattenedTreemapData = budgetTreemapData[0].children.map((item) => ({
    name: item.name,
    size: item.size,
    color: item.color,
  }));

  // Current vs. proposed allocation for pie charts
  const currentAllocationData = channelAllocationData.map((item) => ({
    name: item.name,
    value: item.current,
    color: item.color,
  }));

  const proposedAllocationData = channelAllocationData.map((item) => ({
    name: item.name,
    value: item.proposed,
    color: item.color,
  }));

  // Custom tooltip formatter that ensures value is a number before formatting
  const formatTooltipValue = (value: any) => {
    if (typeof value === 'number') {
      return [`₹${(value/1000).toFixed(1)}K`, ''];
    }
    return [value, ''];
  };

  // Custom tooltip formatter for ROI that ensures value is a number
  const formatROIValue = (value: any) => {
    if (typeof value === 'number') {
      return [`${value.toFixed(1)}x`, 'ROI'];
    }
    return [value, 'ROI'];
  };

  // Custom tooltip formatter for budget that ensures value is a number
  const formatBudgetValue = (value: any) => {
    if (typeof value === 'number') {
      return [`${value.toFixed(1)}%`, 'Allocation'];
    }
    return [value, 'Allocation'];
  };

  // Custom tooltip formatter for percentage values
  const formatPercentageValue = (value: any) => {
    if (typeof value === 'number') {
      return [`${value.toFixed(2)}%`, ''];
    }
    return [value, ''];
  };

  // Calculate the total budget
  const totalBudget = channelAllocationData.reduce((sum, item) => sum + item.current, 0);
  
  // Map icon string names to actual icon components
  const getIconComponent = (iconName: string) => {
    switch (iconName) {
      case 'dollar': return <DollarSign className="h-4 w-4" />;
      case 'trending-up': return <TrendingUp className="h-4 w-4" />;
      case 'bar-chart': return <BarChart3 className="h-4 w-4" />;
      case 'line-chart': return <LineChart className="h-4 w-4" />;
      case 'pie-chart': return <PieChart className="h-4 w-4" />;
      default: return <DollarSign className="h-4 w-4" />;
    }
  };


  
  // Animation variants
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };
  
  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 p-6 overflow-y-auto ml-64">
        <PageHeader
          title="Budget Allocation"
          subtitle="Optimizing marketing budget allocation across channels"
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
          onResetFilters={() => setDateRange(undefined)}
          filters={[
            {
              label: "Budget Year",
              options: [
                { value: "2024", label: "2024" },
                { value: "2023", label: "2023" },
                { value: "2022", label: "2022" },
              ],
              onChange: () => {},
              value: "2024"
            }
          ]}
        />

        {/* Animated Stats Cards */}
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
                value={kpi.value}
                change={null}
                icon={getIconComponent(kpi.icon)}
                delay={i}
                bgGradient={kpi.gradient}
              />
            </motion.div>
          ))}
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <ChartCard
            title="Channel Allocation Percentages by Robyn"
            tooltip="Current vs. proposed percentage allocation by channel"
            size="md"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={channelAllocationData}
                margin={{ top: 20, right: 30, left: 20, bottom: 30 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={70} />
                <YAxis />
                <Tooltip formatter={formatBudgetValue} />
                <Legend />
                <Bar dataKey="current" name="Current Allocation" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="proposed" name="Proposed Allocation" fill="#D946EF" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Monthly Channel Allocation using Bioptimization"
            tooltip="How budget allocation percentages change over months"
            height={300}
          >
            <ResponsiveContainer width="100%" height="100%">
              <ReLineChart
                data={filteredMonthlyChannelData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" />
                <YAxis 
                  yAxisId="left" 
                  domain={[0, 60]} 
                  label={{ value: 'Allocation %', angle: -90, position: 'insideLeft' }} 
                />
                <YAxis 
                  yAxisId="right" 
                  orientation="right" 
                  domain={[0, 'dataMax + 50']} 
                  label={{ value: 'Amount (Cr)', angle: 90, position: 'insideRight' }} 
                />
                
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="TV"
                  name="TV"
                  stroke="#F97316"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="Digital"
                  name="Digital"
                  stroke="#0EA5E9"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="Sponsorship"
                  name="Sponsorship"
                  stroke="#D946EF"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="Content Marketing"
                  name="Content Marketing"
                  stroke="#10B981"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="Online marketing"
                  name="Online Marketing"
                  stroke="#EAB308"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="Affiliates"
                  name="Affiliates"
                  stroke="#8B5CF6"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="SEM"
                  name="SEM"
                  stroke="#EC4899"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />

              </ReLineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <ChartCard
            title="Budget vs. ROI by Channel"
            tooltip="Relationship between budget allocation and ROI"
            size="md"
          >
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart
                margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  dataKey="budget"
                  name="Budget"
                  tickFormatter={(value) => typeof value === 'number' ? `₹${value/1000}K` : value}
                />
                <YAxis type="number" dataKey="roi" name="ROI" />
                <ZAxis type="number" dataKey="size" range={[50, 400]} />
                <Tooltip
                  formatter={(value, name) => {
                    if (name === 'Budget' && typeof value === 'number') return [`₹${(value/1000).toFixed(1)}K`, name];
                    if (name === 'ROI' && typeof value === 'number') return [`${value}x`, name];
                    return [value, name];
                  }}
                  cursor={{ strokeDasharray: '3 3' }}
                />
                <Legend />
                <Scatter
                  name="Channel"
                  data={budgetVsROIData}
                  fill="#8884d8"
                  shape="circle"
                  label={{ dataKey: 'channel', position: 'center', fill: '#fff' }}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Budget Allocation by Sub Categories"
            tooltip="Sub Category distribution of marketing budget"
            size="md"
          >
            <ResponsiveContainer width="100%" height="100%">
              <RePieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <Pie
                  data={subCategoryImportanceData}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name }) => `${name}`}
                >
                  {subCategoryImportanceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={formatBudgetValue} />
              </RePieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <ChartCard
            title="Budget Categories"
            tooltip="Marketing budget breakdown by category and channel"
            size="md"
          >
            <ResponsiveContainer width="100%" height="100%">
              <Treemap
                data={flattenedTreemapData}
                dataKey="size"
                aspectRatio={4/3}
                stroke="#fff"
                fill="#8884d8"
                content={<CustomizedContent colors={flattenedTreemapData.map(item => item.color)} />}
              />
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Current vs. Proposed Allocation"
            tooltip="Comparing current and proposed percentage distributions"
          >
            <div className="grid grid-cols-2 h-full">
              <div className="flex flex-col items-center justify-center">
                <h3 className="text-sm font-medium mb-4">Current Allocation</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <RePieChart>
                    <Pie
                      data={currentAllocationData}
                      cx="50%"
                      cy="50%"
                      labelLine={true}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      nameKey="name"
                      label={({ name, percent }) => 
                        percent > 0.05 ? `${name}: ${(percent * 100).toFixed(1)}%` : null
                      }
                    >
                      {currentAllocationData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={formatBudgetValue} />
                  </RePieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-col items-center justify-center">
                <h3 className="text-sm font-medium mb-4">Proposed Allocation</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <RePieChart>
                    <Pie
                      data={proposedAllocationData}
                      cx="50%"
                      cy="50%"
                      labelLine={true}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      nameKey="name"
                      label={({ name, percent }) => 
                        percent > 0.05 ? `${name}: ${(percent * 100).toFixed(1)}%` : null
                      }
                    >
                      {proposedAllocationData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={formatBudgetValue} />
                  </RePieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 gap-4 mb-4 min-h-[550px]">
          <ChartCard
            title="Budget Allocation Recommendations"
            tooltip="Suggested budget changes based on performance data"
            className="w-full h-full max-h-[700px] overflow-y-auto"
          >
            <Table className="w-full">
              <TableHeader>
                <TableRow>
                  <TableHead>Channel</TableHead>
                  <TableHead>Current Allocation</TableHead>
                  <TableHead>Proposed Allocation</TableHead>
                  <TableHead>Change</TableHead>
                  <TableHead>Recommendation</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {channelAllocationData.map((channel) => {
                  const change = channel.proposed - channel.current;
                  const percentChange = (change / channel.current) * 100;
                  return (
                    <TableRow key={channel.name}>
                      <TableCell className="font-medium">{channel.name}</TableCell>
                      <TableCell>{channel.current.toFixed(1)}%</TableCell>
                      <TableCell>{channel.proposed.toFixed(1)}%</TableCell>
                      <TableCell className={change >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {change >= 0 ? '+' : ''}{percentChange.toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        <span
                          className={`px-2 py-1 rounded-full text-xs ${
                            change > 0
                              ? 'bg-green-100 text-green-800'
                              : change < 0
                                ? 'bg-red-100 text-red-800'
                                : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {change > 0 ? 'Increase' : change < 0 ? 'Decrease' : 'Maintain'}
                        </span>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </ChartCard>
        </div>

        <div className="mb-4">
          <SaturationCurves data={robynSaturationData.channels} />
        </div>

        <div className="mb-4">
          <WhatIfScenario />
        </div>

      </div>
    </div>
  );
};

export default BudgetAllocation;