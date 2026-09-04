import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ExecutiveSummary from "./pages/executive-summary";
import NotFound from "./pages/NotFound";
import BusinessContext from "./pages/business-context";
import MarketingPerformance from "./pages/marketing-performance";
import PerformanceDrivers from "./pages/performance-drivers";
import Index from "./pages/Index";
import MarketingROI from "./pages/marketing-roi";
import BudgetAllocation from "./pages/budget-allocation";
import Implementation from "./pages/implementation";
import Appendix from "./pages/appendix";
import Login from "./pages/login";
import Signup from "./pages/signup";
import Report from "./pages/report"
import { ErrorBoundary } from "@/components/ErrorBoundary";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ErrorBoundary><Index /></ErrorBoundary>} />
          <Route path="/login" element={<ErrorBoundary><Login /></ErrorBoundary>} />
          <Route path="/signup" element={<ErrorBoundary><Signup /></ErrorBoundary>} />
          <Route path="/business-context" element={<ErrorBoundary><BusinessContext /></ErrorBoundary>} />
          <Route path="/marketing-performance" element={<ErrorBoundary><MarketingPerformance /></ErrorBoundary>} />
          <Route path="/performance-drivers" element={<ErrorBoundary><PerformanceDrivers /></ErrorBoundary>} />
          <Route path="/marketing-roi" element={<ErrorBoundary><MarketingROI /></ErrorBoundary>} />
          <Route path="/budget-allocation" element={<ErrorBoundary><BudgetAllocation /></ErrorBoundary>} />
          <Route path="/implementation" element={<ErrorBoundary><Implementation /></ErrorBoundary>} />
          <Route path="/appendix" element={<ErrorBoundary><Appendix /></ErrorBoundary>} />
          <Route path="/executive-summary" element={<ErrorBoundary><ExecutiveSummary /></ErrorBoundary>} />
          <Route path="/report" element={<ErrorBoundary><Report /></ErrorBoundary>} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
