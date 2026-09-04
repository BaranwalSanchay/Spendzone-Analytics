
import React from 'react';
import { Logo } from './logo';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-card border-t py-6">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
            <Logo />
            <p className="text-sm text-muted-foreground mt-2">
              Powering data-driven marketing decisions
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-8">
            <div>
              <h4 className="font-medium mb-2">About</h4>
              <ul className="space-y-1">
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                    Home
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                    Contact
                  </a>
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">Resources</h4>
              <ul className="space-y-1">
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                    Blog
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                    Support
                  </a>
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">Legal</h4>
              <ul className="space-y-1">
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                    Privacy
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                    Terms
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
        
        <div className="mt-8 pt-4 border-t text-center">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} MarketPulse. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};
