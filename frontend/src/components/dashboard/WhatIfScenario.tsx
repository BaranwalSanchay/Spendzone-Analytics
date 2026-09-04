import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { ChartCard } from '@/components/chart-card';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string | undefined;

interface Allocation {
  channel: string;
  amount: number;
  percentage: number;
}

/**
 * Prescriptive "what-if" budget scenario: sends a custom total budget to the
 * backend's /api/budget-scenario endpoint (Spendzone-Analytics/backend/api.py),
 * which re-runs the bi-level optimization's allocation step against the
 * pre-calculated channel weights and returns the exact recommended dollar split.
 */
export const WhatIfScenario: React.FC = () => {
  const [budget, setBudget] = useState('1000000');
  const [allocations, setAllocations] = useState<Allocation[] | null>(null);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const runScenario = async () => {
    const totalBudget = Number(budget);
    if (!Number.isFinite(totalBudget) || totalBudget <= 0) {
      toast({ title: 'Enter a valid budget', variant: 'destructive' });
      return;
    }
    if (!API_BASE_URL) {
      toast({
        title: 'Backend API not configured',
        description: 'Set VITE_API_BASE_URL to use what-if scenarios.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/budget-scenario`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ total_budget: totalBudget }),
      });
      const body = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(body?.detail) ? body.detail[0]?.msg : body?.detail;
        throw new Error(detail || `Request failed (HTTP ${response.status})`);
      }
      setAllocations(body.allocations);
    } catch (error) {
      toast({
        title: 'Could not compute scenario',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">What-If Budget Scenario</h3>
      <p className="text-sm text-muted-foreground">
        Enter a total budget to see the exact dollar split the bi-level optimization model
        recommends across channels.
      </p>

      <div className="flex flex-wrap items-end gap-3">
        <div>
          <Label htmlFor="whatif-budget">Total budget (₹)</Label>
          <Input
            id="whatif-budget"
            type="number"
            min={1}
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            className="w-48"
          />
        </div>
        <Button onClick={runScenario} disabled={loading}>
          {loading ? 'Calculating…' : 'Recommend split'}
        </Button>
      </div>

      {allocations && (
        <ChartCard title="Recommended channel split" height={280}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={allocations} margin={{ top: 10, right: 20, left: 0, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="channel" tick={{ fontSize: 12 }} interval={0} angle={-20} textAnchor="end" height={60} />
              <YAxis tickFormatter={(v: number) => `₹${(v / 1000).toFixed(0)}k`} />
              <Tooltip
                formatter={(value: number) => `₹${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
              />
              <Bar dataKey="amount" name="Recommended spend" fill="#38B2AC" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}
    </div>
  );
};
