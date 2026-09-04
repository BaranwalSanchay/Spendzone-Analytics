import React from 'react';
import { Sidebar } from '@/components/sidebar';
import { PageHeader } from '@/components/page-header';
import { StatsCard } from '@/components/stats-card';
import { ChartCard } from '@/components/chart-card';
import { LineChart, BarChart3, Target, Award, Folders, CheckCircle, DollarSign, Clock, Users } from 'lucide-react';
import { motion } from "framer-motion";
import StatCard from '@/components/dashboard/StatCard';
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
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Area,
  ScatterChart,
  Scatter,
  ZAxis,
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ReferenceLine
} from 'recharts';
import dashboardData from '../../public/data/dashboardData.json';

const Implementation: React.FC = () => {
  // Import data from dashboardData.json
  const {
    implementationStatusData,
    taskEffectivenessData,
    taskEffectivenessBarData,
    timelineData,
    timelineBarData,
    implementationByChannelData,
    channelImplementationBarData,
    kpiTrackingData,
    resourceAllocationData,
    implementationTasksData,
    teamPerformanceData,
    teamPerformanceBarData,
    kpiData
  } = dashboardData.implementation;

  
  // Colors for positive and negative values
  const positiveColor = "#10B981"; // green
  const negativeColor = "#EF4444"; // red
  
  // Status colors for tasks
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Expected': return 'bg-green-100 text-green-800';
      case 'Upcoming': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Priority colors
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'High': return 'bg-red-100 text-red-800';
      case 'Medium': return 'bg-orange-100 text-orange-800';
      case 'Low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Map icon string names to actual components
  const getIconComponent = (iconName: string) => {
    switch (iconName) {
      case 'Folders': return <Folders className="h-4 w-4" />;
      case 'CheckCircle': return <CheckCircle className="h-4 w-4" />;
      case 'DollarSign': return <DollarSign className="h-4 w-4" />;
      case 'Clock': return <Clock className="h-4 w-4" />;
      case 'Users': return <Users className="h-4 w-4" />;
      case 'LineChart': return <LineChart className="h-4 w-4" />;
      case 'BarChart3': return <BarChart3 className="h-4 w-4" />;
      case 'Target': return <Target className="h-4 w-4" />;
      case 'Award': return <Award className="h-4 w-4" />;
      default: return <BarChart3 className="h-4 w-4" />;
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
          title="Implementation Tracking"
          subtitle="Monitor progress of marketing initiatives and campaigns"
          filters={[
            {
              label: "Project",
              options: [
                { value: "all", label: "All Projects" },
                { value: "q2-campaign", label: "Q2 Campaign" },
                { value: "rebranding", label: "Rebranding" },
              ],
              onChange: () => {},
              value: "all"
            }
          ]}
        />

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
                icon={getIconComponent(kpi.icon || 'dollar')} // Use the icon component directly
                delay={i}
                bgGradient={kpi.gradient}
              />
            </motion.div>
          ))}
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <ChartCard
            title="Camera"
            tooltip="Task effectiveness compared to previous performance and goals"
            height={300}
            size="md"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={taskEffectivenessBarData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="previous" name="Previous" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="current" name="Current" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="CameraAccessory"
            tooltip="Quarterly task completion vs. targets and previous performance"
            height={300}
            size="md"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={timelineBarData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="previous" name="Previous" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="current" name="Current" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="EntertainmentSmall"
            tooltip="Implementation progress by marketing channel"
            height={300}
            size="md"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={channelImplementationBarData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="previous" name="Previous" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="current" name="Current" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <ChartCard
            title="GameCDDVD"
            tooltip="KPI tracking against goals and previous performance"
          >
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={kpiTrackingData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="previous" name="Previous" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="actual" name="Current" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="GamingHardware"
            tooltip="Performance metrics for implementation teams"
          >
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={teamPerformanceBarData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="previous" name="Previous" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="current" name="Current" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          {/* <div className="col-span-1">
            <ChartCard
              title="Resource Allocation"
              tooltip="Distribution of resources across implementation areas"
              size="md"
              height={400}
            >
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={resourceAllocationData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                  >
                    {resourceAllocationData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value}%`, 'Allocation']} />
                  <Legend layout="vertical" verticalAlign="bottom" align="center" />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          </div> */}

          <div className="col-span-4">
            <ChartCard
              title="Sales Calender"
              tooltip="Detailed view of Sales Timeline and their status"
              size="md"
              height={600}
            >
              <div className="overflow-auto max-h-[600px]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Task</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Team</TableHead>
                      <TableHead>Due Date</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Revenue (Cr)</TableHead>
                      <TableHead>Total Days</TableHead>
                      <TableHead>Schedules</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {implementationTasksData.map((task) => (
                      <TableRow key={task.id}>
                        <TableCell className="font-medium">{task.task}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(task.status)}`}>
                            {task.status}
                          </span>
                        </TableCell>
                        <TableCell>{task.Team}</TableCell>
                        <TableCell>{new Date(task.Date).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded-full text-xs ${getPriorityColor(task.priority)}`}>
                            {task.priority}
                          </span>
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          ₹{task.revenue}
                        </TableCell>
                        <TableCell className="text-center">
                          {task.totalDays}
                        </TableCell>
                        <TableCell>
                          {task.schedules.length > 0 ? (
                            <div className="flex flex-col gap-1">
                              {task.schedules.map((schedule, idx) => (
                                <div key={idx} className="flex items-center text-xs">
                                  <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-blue-100 text-blue-800 mr-2">
                                    <Clock className="h-3 w-3" />
                                  </span>
                                  {schedule
                                    .replace("second Tuesday", "2nd Tue")
                                    .replace("fourth Wednesday", "4th Wed")
                                    .replace("second Wednesday", "2nd Wed")
                                    .replace("fourth Tuesday", "4th Tue")}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <span className="text-xs text-gray-400 italic">No scheduled campaigns</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </ChartCard>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Implementation;