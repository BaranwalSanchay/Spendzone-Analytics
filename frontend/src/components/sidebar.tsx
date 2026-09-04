import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate} from 'react-router-dom';
import { cn } from '@/lib/utils';
import { 
  BarChart3, 
  PieChart, 
  TrendingUp, 
  DollarSign, 
  BarChart, 
  LineChart, 
  Layout, 
  FileText, 
  Briefcase,
  ChevronRight,
  ChevronLeft,
  FileBarChart,
  Menu
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import type { User } from '@supabase/supabase-js';

interface SidebarItemProps {
  href: string;
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  collapsed?: boolean;
}

const Logo = ({ collapsed }: { collapsed?: boolean }) => (
  <Link to="/" className="block">
    <div className={cn("flex justify-center items-center py-6", collapsed ? "px-0" : "")}>
      <div className={cn("bg-gradient-to-br from-teal-400 to-teal-600 rounded-md flex items-center justify-center shadow-lg", 
        collapsed ? "h-10 w-10" : "h-14 w-14")}>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={cn(collapsed ? "h-6 w-6" : "h-8 w-8")}>
          <rect x="2" y="2" width="8" height="8" rx="1"></rect>
          <path d="M14 2l6 6-6 6"></path>
          <rect x="2" y="14" width="8" height="8" rx="1"></rect>
        </svg>
      </div>
    </div>
  </Link>
);

const SidebarItem: React.FC<SidebarItemProps> = ({ href, icon, label, active, collapsed }) => {
  return (
    <Link
      to={href}
      className={cn(
        "flex items-center gap-3 rounded-md transition-colors",
        collapsed ? "justify-center px-0 py-3" : "px-3 py-2",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/80 hover:text-sidebar-foreground hover:bg-sidebar-accent/50"
      )}
      title={collapsed ? label : undefined}
    >
      <div className={cn("flex-shrink-0", collapsed ? "w-5 h-5 mx-auto" : "w-5 h-5")}>{icon}</div>
      {!collapsed && <span className="text-sm font-medium">{label}</span>}
    </Link>
  );
};

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const pathname = location.pathname;
  const [user, setUser] = useState<User | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  // Track the live Supabase auth session
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Load collapsed state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState) {
      setCollapsed(savedState === 'true');
    }
  }, []);

  // Save collapsed state to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', collapsed.toString());
    // Update body class to adjust main content
    if (collapsed) {
      document.body.classList.add('sidebar-collapsed');
    } else {
      document.body.classList.remove('sidebar-collapsed');
    }
  }, [collapsed]);

  // Toggle sidebar collapse state
  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  // Update handleGenerateReport to navigate
  const handleGenerateReport = async () => {
    if (!user) {
      toast({
        title: 'Authentication required',
        description: 'Please log in to generate reports',
        variant: 'destructive'
      });
      return;
    }

    const { data: datasets } = await supabase
      .from('datasets')
      .select('id')
      .eq('owner_id', user.id)
      .limit(1);

    if (!datasets || datasets.length === 0) {
      toast({
        title: 'No data available',
        description: 'Please upload your marketing data first',
        variant: 'destructive'
      });
      return;
    }

    navigate('/report');
  };

  const sidebarItems = [
    { href: "/executive-summary", icon: <Layout />, label: "Executive Summary" },
    { href: "/business-context", icon: <Briefcase />, label: "Business Context" },
    { href: "/marketing-performance", icon: <TrendingUp />, label: "Marketing Performance" },
    { href: "/performance-drivers", icon: <BarChart />, label: "Performance Drivers" },
    { href: "/marketing-roi", icon: <PieChart />, label: "Marketing ROI" },
    { href: "/budget-allocation", icon: <DollarSign />, label: "Budget Allocation" },
    { href: "/implementation", icon: <LineChart />, label: "Implementation" },
    { href: "/appendix", icon: <FileText />, label: "Appendix" },
  ];

  return (
    <div className={cn(
      "fixed h-screen bg-sidebar flex flex-col border-r overflow-hidden transition-all duration-300",
      collapsed ? "w-16" : "w-64"
    )}>
      {/* Logo Section */}
      <div className="border-b border-sidebar-accent/30 mb-2 relative">
        <Logo collapsed={collapsed} />
        {!collapsed && (
          <Link to="/" className="block text-center pb-4">
            <h2 className="font-bold text-xl text-white">Spendzone</h2>
            <p className="text-xs text-sidebar-foreground/60">Budget Optimizer</p>
          </Link>
        )}
        
        {/* Collapse toggle button */}
        <Button 
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="absolute right-2 top-2 h-6 w-6 text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-accent/30"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </Button>
      </div>
      
      {/* Visual Divider */}
      <div className={cn(
        "h-0.5 bg-gradient-to-r from-transparent via-sidebar-accent/30 to-transparent mb-4",
        collapsed ? "mx-2" : "mx-4"
      )}></div>
      
      {/* Navigation Items */}
      <div className="flex-1 py-2 space-y-1 px-2 overflow-hidden">
        {sidebarItems.map((item) => (
          <SidebarItem
            key={item.href}
            href={item.href}
            icon={item.icon}
            label={item.label}
            active={pathname === item.href}
            collapsed={collapsed}
          />
        ))}
      </div>
      
      {/* Report Button at Bottom */}
      <div className={cn(
        "border-t border-sidebar-accent/20 mt-auto",
        collapsed ? "p-2" : "p-4"
      )}>
        {collapsed ? (
          <Button 
            variant="outline" 
            size="icon" 
            onClick={handleGenerateReport}
            className="w-full h-10 flex items-center justify-center"
            title="Generate Report"
          >
            <FileText className="h-4 w-4" />
          </Button>
        ) : (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleGenerateReport}
            className="w-full flex items-center justify-center gap-2"
          >
            <FileText className="h-4 w-4" />
            <span>Generate Report</span>
          </Button>
        )}
        
        {!collapsed && (
          <div className="mt-4 text-xs text-sidebar-foreground/60">
            <p>© {new Date().getFullYear()} Spendzone</p>
            <p>Version 1.2.0</p>
          </div>
        )}
      </div>
    </div>
  );
};
