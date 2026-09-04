import React, {useState, useEffect} from "react";
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
  ComposedChart,
  Treemap,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  DollarSign,
  TrendingUp,
  BarChart3,
  ShoppingCart,
  LineChartIcon,
  PieChartIcon,
} from "lucide-react";

// Define interfaces for our data types
interface MonthlyRevenueItem {
  month: string;
  revenue: number;
  marketingSpend: number;
}

interface CategoryRevenueItem {
  name: string;
  value: number;
}

interface QuarterlyRevenueItem {
  name: string;
  Smartphones: number;
  Laptops: number;
  Televisions: number;
  Audio: number;
  Cameras: number;
  Gaming: number;
  Wearables: number;
  Accessories: number;
}

interface ChannelSpendItem {
  quarter: string;
  [key: string]: any; // For dynamic channel names
}

interface MarketShareItem {
  name: string;
  value: number;
}

interface AnnualChannelSpendItem {
  name: string;
  value: number;
}

interface ChangeData {
  value: number;
  positive: boolean;
}

interface KpiDataItem {
  title: string;
  value: string;
  change: ChangeData;
  icon: string;
  gradient: string;
}

// Update the interfaces section to include SaleDaysItem
interface SaleDaysItem {
  year: number;
  month: number;
  monthName: string;
  sale_days: number;
}

interface DashboardData {
  monthlyRevenueData: MonthlyRevenueItem[];
  categoryRevenueData: CategoryRevenueItem[];
  quarterlyRevenueData: QuarterlyRevenueItem[];
  channelSpendData: ChannelSpendItem[];
  marketShareData: MarketShareItem[];
  annualChannelSpendData: AnnualChannelSpendItem[];
  kpiData: KpiDataItem[];
  saleDaysData: SaleDaysItem[]; // Add this line
}

const BusinessContext = () => {
  // State for dashboard data
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/data/dashboardData.json');
        const data = await response.json();
        setDashboardData(data['business-context']);
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
      <div className="min-h-screen flex flex-col">
        <div className="flex-1 flex">
          <Sidebar />
          <div className="flex-1 p-8 ml-64 flex items-center justify-center">
            <p>Loading dashboard data...</p>
          </div>
        </div>
      </div>
    );
  }

  // For demo filters
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
      label: "Region",
      options: [
        { value: "all", label: "All Regions" },
        { value: "ontario", label: "Ontario" },
        { value: "quebec", label: "Quebec" },
        { value: "british-columbia", label: "British Columbia" },
      ],
      onChange: () => {},
      value: "all",
    },
  ];

  // Colors for charts
  const COLORS = ['#38B2AC', '#4FD1C5', '#81E6D9', '#2D3748', '#4A5568', '#F6AD55', '#F6E05E', '#9AE6B4'];
  
  // Extract data from the dashboardData
  const { 
    monthlyRevenueData, 
    categoryRevenueData, 
    quarterlyRevenueData, 
    channelSpendData, 
    marketShareData,
    annualChannelSpendData,
    kpiData,
    saleDaysData = [] // Add default empty array in case it's undefined
  } = dashboardData;
  
  // Add this console log to debug
  console.log("Sale Days Data:", saleDaysData);
  
  // Calculate yearly totals for stats cards
  const yearlyRevenue = monthlyRevenueData.reduce(
    (sum, item) => sum + item.revenue,
    0
  );
  const yearlySpend = monthlyRevenueData.reduce(
    (sum, item) => sum + item.marketingSpend,
    0
  );
  const yearlyROI = (yearlyRevenue / yearlySpend).toFixed(2);
  const marketSharePercentage = marketShareData.find(item => item.name === 'ElectroMart')?.value || 0;
  
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

  // Get icon component based on string name
  const getIconComponent = (iconName: string) => {
    switch (iconName) {
      case 'dollar': return <DollarSign className="h-4 w-4" />;
      case 'trending-up': return <TrendingUp className="h-4 w-4" />;
      case 'bar-chart': return <BarChart3 className="h-4 w-4" />;
      case 'shopping-cart': return <ShoppingCart className="h-4 w-4" />;
      case 'line-chart': return <LineChartIcon className="h-4 w-4" />;
      case 'pie-chart': return <PieChartIcon className="h-4 w-4" />;
      default: return <DollarSign className="h-4 w-4" />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex">
        <Sidebar />

        <main className="flex-1 p-6 overflow-y-auto ml-64">
          <PageHeader
            title="Business Context"
            subtitle="Market trends, competitive landscape, and business performance"
            filters={filters}
          />

          {/* Stats Row - Animated with Framer Motion */}
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
                  change={kpi.change}
                  icon={getIconComponent(kpi.icon || 'dollar')}
                  delay={i}
                  bgGradient={kpi.gradient}
                />
              </motion.div>
            ))}
          </motion.div>

          {/* First row of charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <ChartCard title="Number of Sale Days per Month" tooltip="Shows the number of promotional sale days in each month" height={320}>
            <ResponsiveContainer width="100%" height="100%">
              {saleDaysData && saleDaysData.length > 0 ? (
                <BarChart data={saleDaysData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis 
                    dataKey="monthName" 
                    tickFormatter={(value, index) => {
                      const item = saleDaysData[index];
                      return item ? `${value} ${item.year}` : value;
                    }}
                  />
                  <YAxis domain={[0, 10]} />
                  <Tooltip 
                    formatter={(value) => [`${value} days`, 'Sale Days']}
                    labelFormatter={(label, payload) => {
                      if (payload && payload.length > 0) {
                        const item = payload[0].payload;
                        return item.year ? `${label} ${item.year}` : label;
                      }
                      return label;
                    }}
                  />
                  <Legend />
                  <Bar 
                    dataKey="sale_days" 
                    name="Sale Days" 
                    fill="#F59E0B"
                    radius={[4, 4, 0, 0]}
                    label={{
                      position: 'top',
                      formatter: (value) => `${value}`,
                      fill: '#666',
                      fontSize: 12
                    }}
                  />
                </BarChart>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p>No sale days data available</p>
                </div>
              )}
            </ResponsiveContainer>
          </ChartCard>

            
            <ChartCard title="Product Distribution By Price Range" height={320}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={marketShareData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {marketShareData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Second row of charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <ChartCard title="Revenue by Category" height={320}>
              <ResponsiveContainer width="100%" height="100%">
                <Treemap
                  data={categoryRevenueData}
                  dataKey="value"
                  nameKey="name"
                  aspectRatio={4 / 3}
                  stroke="#fff"
                >
                  <Tooltip
                    formatter={(value: any) =>
                      `$${(Number(value) / 1000000).toFixed(2)}M`
                    }
                  />
                </Treemap>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Quarterly Revenue by Category" height={320}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={quarterlyRevenueData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => `$${(Number(value)).toLocaleString()}`} />
                  <Legend />
                  <Bar dataKey="Camera" stackId="a" fill="#38B2AC" />
                  <Bar dataKey="EntertainmentSmall" stackId="a" fill="#4FD1C5" />
                  <Bar dataKey="GamingHardware" stackId="a" fill="#81E6D9" />
                  <Bar dataKey="CameraAccessory" stackId="a" fill="#2D3748" />
                  <Bar dataKey="GameCDDVD" stackId="a" fill="#4A5568" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Third row of charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <ChartCard title="Quarterly Marketing Channel Spend" height={320}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={channelSpendData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="quarter" />
                  <YAxis />
                  <Tooltip formatter={(value) => `₹${value} M`} />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="TV" 
                    stackId="1" 
                    fill="#38B2AC" 
                    stroke="#38B2AC"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="Digital" 
                    stackId="1" 
                    fill="#4FD1C5" 
                    stroke="#4FD1C5"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="Content Marketing" 
                    stackId="1" 
                    fill="#81E6D9" 
                    stroke="#81E6D9"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="Online Marketing" 
                    stackId="1" 
                    fill="#2D3748" 
                    stroke="#2D3748"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="Sponsorship" 
                    stackId="1" 
                    fill="#F6AD55" 
                    stroke="#F6AD55"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Marketing ROI Trend" height={320}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={monthlyRevenueData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip
                    formatter={(value, name) => {
                      if (name === "ROI") return `${value}x`;
                      return value;
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey={(data) =>
                      (data.revenue / data.marketingSpend).toFixed(2)
                    }
                    name="ROI"
                    stroke="#38B2AC"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Final row of charts */}
          <div className="grid grid-cols-1 gap-6 mb-6">
            <ChartCard title="Annual Marketing Spend by Channel" height={320}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  layout="vertical"
                  data={annualChannelSpendData}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    horizontal={true}
                    vertical={false}
                  />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={100} />
                  <Tooltip formatter={(value) => `₹${value} M`} />
                  <Bar 
                    dataKey="value" 
                    name="Marketing Spend" 
                    fill="#38B2AC"
                    label={{
                      position: 'right',
                      formatter: (value) => `₹${value} M`,
                    }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
        </main>
      </div>
    </div>
  );
};

export default BusinessContext;
