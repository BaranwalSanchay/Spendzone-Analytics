import React, { ReactNode } from 'react';
import { Sidebar } from '@/components/sidebar';
import { Footer } from '@/components/footer';

interface DashboardLayoutProps {
  children: ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className="ml-64 min-h-screen"> {/* ml-64 equals the width of sidebar */}
        <main className="p-6 pb-16">
          {children}
        </main>
        <Footer />
      </div>
    </div>
  );
}; 