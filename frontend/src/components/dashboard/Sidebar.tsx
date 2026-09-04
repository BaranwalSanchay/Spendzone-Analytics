
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  BarChart3,
  LineChart,
  PieChart,
  TrendingUp,
  DollarSign,
  CalendarCheck,
  ClipboardList,
} from "lucide-react";
import { 
  Sidebar as SidebarComponent, 
  SidebarContent, 
  SidebarMenu, 
  SidebarMenuItem, 
  SidebarMenuButton,
  SidebarTrigger,
  useSidebar
} from "@/components/ui/sidebar";

interface NavItem {
  title: string;
  href: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    title: "Executive Summary",
    href: "/dashboard/executive-summary",
    icon: <LayoutDashboard className="h-5 w-5" />,
  },
  {
    title: "Business Context",
    href: "/dashboard/business-context",
    icon: <BarChart3 className="h-5 w-5" />,
  },
  {
    title: "Marketing Performance",
    href: "/dashboard/marketing-performance",
    icon: <TrendingUp className="h-5 w-5" />,
  },
  {
    title: "Performance Drivers",
    href: "/dashboard/performance-drivers",
    icon: <LineChart className="h-5 w-5" />,
  },
  {
    title: "Marketing ROI",
    href: "/dashboard/marketing-roi",
    icon: <DollarSign className="h-5 w-5" />,
  },
  {
    title: "Budget Allocation",
    href: "/dashboard/budget-allocation",
    icon: <PieChart className="h-5 w-5" />,
  },
  {
    title: "Implementation",
    href: "/dashboard/implementation",
    icon: <CalendarCheck className="h-5 w-5" />,
  },
  {
    title: "Appendix",
    href: "/dashboard/appendix",
    icon: <ClipboardList className="h-5 w-5" />,
  },
];

const Sidebar = () => {
  const location = useLocation();
  const { state } = useSidebar();

  return (
    <>
      <div className="absolute top-4 left-4 z-50 md:hidden">
        <SidebarTrigger />
      </div>
      
      <SidebarComponent variant="sidebar" collapsible="icon">
        <SidebarContent className="pt-16">
          <SidebarMenu>
            {navItems.map((item) => (
              <SidebarMenuItem key={item.href}>
                <SidebarMenuButton
                  asChild
                  isActive={location.pathname === item.href}
                  tooltip={state === "collapsed" ? item.title : undefined}
                >
                  <Link to={item.href}>
                    {item.icon}
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarContent>
      </SidebarComponent>
    </>
  );
};

export default Sidebar;
