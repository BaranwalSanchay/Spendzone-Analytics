import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowRight, Upload, BarChart2, LineChart, PieChart, TrendingUp, Star } from 'lucide-react';
import { DataUploadCard } from '@/components/data-upload-card';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/header';
import { Footer } from '@/components/footer';
import { Logo } from '@/components/logo';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import type { User } from '@supabase/supabase-js';

// Scroll animation hook
const useScrollAnimation = () => {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("animate");
          }
        });
      },
      { threshold: 0.1 }
    );

    document.querySelectorAll(".animate-on-scroll").forEach((element) => {
      observer.observe(element);
    });

    return () => observer.disconnect();
  }, []);
};

const Index: React.FC = () => {
  useScrollAnimation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [hasUploadedData, setHasUploadedData] = useState(false);

  const checkForUploadedData = async (currentUser: User | null) => {
    if (!currentUser) {
      setHasUploadedData(false);
      return;
    }

    const { data: datasets } = await supabase
      .from('datasets')
      .select('id')
      .eq('owner_id', currentUser.id)
      .limit(1);

    setHasUploadedData(!!datasets && datasets.length > 0);
  };

  // Track the live Supabase auth session and refresh upload status alongside it
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      checkForUploadedData(session?.user ?? null);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      checkForUploadedData(session?.user ?? null);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const handleSuccessfulUpload = () => {
    setHasUploadedData(true);
    toast({
      title: "Data uploaded successfully",
      description: "You can now view your dashboard or generate reports.",
    });
  };

  const handleUploadClick = () => {
    if (!user) {
      toast({
        title: "Authentication Required",
        description: "Please log in to upload data.",
        variant: "destructive"
      });
      navigate('/login');
      return;
    }
    
    // Instead of opening modal, scroll to the upload section
    const uploadSection = document.getElementById('upload-section');
    if (uploadSection) {
      uploadSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-background via-background to-secondary/20">
      {/* Nav */}
      <Header />
      
      <main className="flex-1">
        <div className="animate-on-scroll">
          <Hero 
            user={user} 
            hasUploadedData={hasUploadedData} 
            handleUploadClick={handleUploadClick} 
            navigate={navigate} 
          />
        </div>
        <div className="animate-on-scroll">
          <Features />
        </div>
        <div className="animate-on-scroll">
          <CTA navigate={navigate} />
        </div>
        
        {/* Data Upload Section - Only shown if user is logged in */}
        {user && (
          <section id="upload-section" className="py-16 bg-muted">
            <div className="container mx-auto px-4">
              <div className="max-w-3xl mx-auto">
                <DataUploadCard
                  onSuccess={() => {
                    handleSuccessfulUpload();
                    checkForUploadedData(user);
                  }}
                  onViewDashboard={() => navigate('/executive-summary')}
                  onGenerateReport={() => navigate('/report')}
                />
                {/* Remove the buttons div that was here */}
              </div>
            </div>
          </section>
        )}
      </main>
      
      <Footer />
      
      {/* Remove the Dialog component since we're using scroll instead */}
    </div>
  );
};

// Hero component with animated elements
const Hero = ({ user, hasUploadedData, handleUploadClick, navigate }: any) => {
  return (
    <div className="relative overflow-hidden">
      {/* Dynamic animated background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-secondary/30 animate-gradient-slow"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(120,190,230,0.15),transparent)]"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(var(--primary),0.1),transparent)]"></div>
      
      {/* Animated design elements */}
      <div className="absolute top-20 right-10 w-72 h-72 bg-primary/5 rounded-full blur-3xl"></div>
      <div className="absolute bottom-20 left-10 w-72 h-72 bg-blue-500/5 rounded-full blur-3xl"></div>
      <div className="absolute top-1/2 left-1/2 w-72 h-72 bg-purple-500/5 rounded-full blur-3xl"></div>

      {/* Floating elements */}
      <div className="absolute top-20 left-[20%] w-8 h-8 border border-primary/20 rounded-lg"></div>
      <div className="absolute bottom-20 right-[20%] w-8 h-8 border border-primary/20 rounded-full"></div>
      
      <div className="relative container mx-auto px-4 py-16 md:py-24 lg:py-32">
        <div className="grid gap-6 lg:grid-cols-2 lg:gap-12">
          <div className="flex flex-col justify-center space-y-8">
            <div className="space-y-6">
              <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl leading-[1.1] pb-1 bg-gradient-to-r from-primary via-blue-600 to-primary bg-clip-text text-transparent">
                Marketing Insights at Your Fingertips
              </h1>
              <p className="max-w-prose text-muted-foreground text-lg md:text-xl pt-2">
                Analyze, optimize, and allocate your marketing spend for maximum ROI using advanced analytics and interactive dashboards.
              </p>
            </div>
            <div className="flex flex-col gap-4 sm:flex-row">
              <Button
                className="group"
                size="lg"
                onClick={handleUploadClick}
              >
                <span>Upload Data</span>
                <Upload className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
              {hasUploadedData && (
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => navigate("/executive-summary")}
                >
                  <span>View Dashboard</span>
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              )}
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Star className="h-4 w-4 fill-primary text-primary" />
                <Star className="h-4 w-4 fill-primary text-primary" />
                <Star className="h-4 w-4 fill-primary text-primary" />
                <Star className="h-4 w-4 fill-primary text-primary" />
                <Star className="h-4 w-4 fill-primary text-primary" />
              </div>
              <div>
                Trusted by over 1,000+ marketing teams worldwide
              </div>
            </div>
          </div>
          <div className="relative mt-8 lg:mt-0">
            <div className="relative rounded-xl border bg-background/50 backdrop-blur-sm shadow-xl">
              <div className="absolute -top-4 -left-4 right-4 bottom-4 rounded-xl border border-primary/10 bg-primary/5"></div>
              <img
                src="assets\image.png"
                alt="Dashboard preview"
                className="rounded-xl w-full h-auto object-cover"
                width={600}
                height={400}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Features section
const Features = () => {
  const features = [
    {
      icon: <BarChart2 className="h-10 w-10" />,
      title: "Performance Analytics",
      description: "Track marketing performance across all channels and campaigns.",
    },
    {
      icon: <LineChart className="h-10 w-10" />,
      title: "Budget Optimization",
      description: "Distribute your marketing budget for maximum impact and ROI.",
    },
    {
      icon: <PieChart className="h-10 w-10" />,
      title: "Channel Insights",
      description: "Understand which marketing channels drive the most value.",
    },
    {
      icon: <TrendingUp className="h-10 w-10" />,
      title: "ROI Forecasting",
      description: "Predict future performance based on historical data and trends.",
    },
  ];

  return (
    <div className="bg-white dark:bg-gray-950 py-16 md:py-24">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold tracking-tight">Powerful Features</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Everything you need to analyze and optimize your marketing investments
          </p>
        </div>
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {features.map((feature, index) => (
            <div
              key={index}
              className="rounded-xl border bg-background p-6 shadow-sm transition-all duration-200 hover:shadow-md"
            >
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
                {feature.icon}
              </div>
              <h3 className="mb-2 text-xl font-medium">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Call to action section
const CTA = ({ navigate }: any) => {
  return (
    <div className="bg-primary-50 dark:bg-gray-900 py-16 md:py-24">
      <div className="container mx-auto px-4">
        <div className="rounded-2xl bg-gradient-to-br from-primary/90 to-primary/70 p-8 md:p-12 lg:p-16 text-white shadow-lg">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
              Ready to optimize your marketing budget?
            </h2>
            <p className="mt-4 text-lg opacity-90">
              Upload your data now and get actionable insights to maximize your marketing ROI.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row justify-center gap-4">
              <Button
                size="lg"
                variant="outline"
                className="border-white bg-white/10 text-white hover:bg-white/20"
                onClick={() => navigate("/login")}
              >
                Get Started
              </Button>
              <Button
                size="lg"
                className="bg-white text-primary hover:bg-white/90"
                onClick={() => navigate("/executive-summary")}
              >
                View Demo
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
