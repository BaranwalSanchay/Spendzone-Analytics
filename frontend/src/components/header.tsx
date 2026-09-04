import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel
} from '@/components/ui/dropdown-menu';
import { FileUp, FileText, LogOut, Settings, User, Bell } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import type { User as SupabaseUser } from '@supabase/supabase-js';

// Custom Logo component based on gc-dashboard-1
const Logo = () => (
  <a href="/" className="flex items-center gap-2">
    <div className="h-8 w-8 bg-gradient-to-br from-teal-400 to-teal-600 rounded-md flex items-center justify-center">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <rect x="2" y="2" width="8" height="8" rx="1"></rect>
        <path d="M14 2l6 6-6 6"></path>
        <rect x="2" y="14" width="8" height="8" rx="1"></rect>
      </svg>
    </div>
    <span className="font-semibold text-lg tracking-tight">Spendzone</span>
  </a>
);

export const Header: React.FC = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [user, setUser] = useState<SupabaseUser | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

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

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setUser(null);
    toast({
      title: 'Logged out',
      description: 'You have been successfully logged out.',
    });
    navigate('/');
  };

  const handleUpload = () => {
    if (!user) {
      toast({
        title: 'Authentication required',
        description: 'Please log in to upload data',
        variant: 'destructive'
      });
      return;
    }
    setUploadModalOpen(true);
  };

  const handleGenerateReport = async () => {
    if (!user) {
      toast({
        title: 'Authentication required',
        description: 'Please log in to generate reports',
        variant: 'destructive'
      });
      return;
    }

    // Check if the user has uploaded any datasets
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

  const handleFileUploadSubmit = (files: FileList | null) => {
    if (files && files.length > 0) {
      const fileNames = Array.from(files).map(file => file.name).join(', ');
      toast({
        title: 'Files uploaded',
        description: `Successfully uploaded: ${fileNames}`,
      });
      setUploadModalOpen(false);
    }
  };

  // Get user's display name or initial for avatar
  const getUserDisplayName = () => {
    if (!user) return '';

    const metadata = user.user_metadata ?? {};
    if (metadata.full_name) return metadata.full_name;
    if (metadata.name) return metadata.name;
    if (user.email) return user.email.split('@')[0];
    if (user.phone) return `User ${user.phone.slice(-4)}`;

    return 'User';
  };

  const getAvatarUrl = () => user?.user_metadata?.avatar_url ?? user?.user_metadata?.picture;
  
  // Get avatar fallback (initials)
  const getAvatarFallback = () => {
    const displayName = getUserDisplayName();
    return displayName.charAt(0).toUpperCase();
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur-sm">
      <div className="container flex h-16 items-center justify-between">
        <Logo />
        
        <div className="flex items-center gap-4">
          {user ? (
            <>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleUpload}
                className="hidden sm:flex items-center gap-1"
              >
                <FileUp className="h-4 w-4" />
                <span>Upload</span>
              </Button>
              
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleGenerateReport}
                className="hidden sm:flex items-center gap-1"
              >
                <FileText className="h-4 w-4" />
                <span>Report</span>
              </Button>

              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-5 w-5" />
                <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-primary"></span>
              </Button>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={getAvatarUrl()} alt={getUserDisplayName()} />
                      <AvatarFallback>{getAvatarFallback()}</AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">{getUserDisplayName()}</p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {user.email || user.phone || ''}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate('/executive-summary')}>
                    Dashboard
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleUpload}>
                    Upload Data
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/report')}>
                    Generate Report
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut className="h-4 w-4 mr-2" />
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <Link to="/login">
              <Button size="sm">
                Log in
              </Button>
            </Link>
          )}
        </div>
      </div>

      <Dialog open={uploadModalOpen} onOpenChange={setUploadModalOpen}>
        <DialogContent className="sm:max-w-[485px]">
          <DialogHeader>
            <DialogTitle>Upload Data</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <p className="text-sm text-muted-foreground">
                Upload CSV files containing your marketing data. The data will be processed and available in your dashboard.
              </p>
              <div className="flex items-center justify-center w-full">
                <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:hover:bg-gray-800 hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-700">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <FileUp className="w-8 h-8 mb-3 text-gray-400" />
                    <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                      <span className="font-semibold">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">CSV, Excel, or JSON files</p>
                  </div>
                  <input 
                    id="dropzone-file" 
                    type="file" 
                    className="hidden" 
                    accept=".csv,.xlsx,.json" 
                    multiple
                    onChange={(e) => handleFileUploadSubmit(e.target.files)}
                  />
                </label>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </header>
  );
};
