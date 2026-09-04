import React, { useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceDot,
} from 'recharts';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ChartCard } from '@/components/chart-card';

export interface ChannelSaturation {
  channel: string;
  /** Hill function shape parameter (steepness of the curve) */
  alpha: number;
  /** Hill function inflexion point, as a fraction (0-1) of maxObservedSpend */
  gamma: number;
  /** Geometric adstock decay rate (0-1): share of this period's effect that carries into the next */
  theta?: number;
  /** Largest historical spend observed for this channel — scales the curve's x-axis */
  maxObservedSpend: number;
  /** Optional marker for the channel's current/most recent spend level */
  currentSpend?: number;
}

interface Props {
  data: ChannelSaturation[];
}

const CURVE_STEPS = 60;
const ADSTOCK_MONTHS = 12;

/** Robyn's Hill saturation transform: response = x^alpha / (x^alpha + inflexion^alpha) */
function hillSaturation(spend: number, alpha: number, gamma: number, maxSpend: number): number {
  if (spend <= 0 || maxSpend <= 0) return 0;
  const inflexion = gamma * maxSpend;
  const spendAlpha = Math.pow(spend, alpha);
  const inflexionAlpha = Math.pow(inflexion, alpha);
  return spendAlpha / (spendAlpha + inflexionAlpha);
}

export const SaturationCurves: React.FC<Props> = ({ data }) => {
  const [selected, setSelected] = useState<string>(data[0]?.channel ?? '');
  const channel = data.find((c) => c.channel === selected) ?? data[0];

  const curve = useMemo(() => {
    if (!channel) return [];
    const domainMax = channel.maxObservedSpend * 1.4;
    return Array.from({ length: CURVE_STEPS + 1 }, (_, i) => {
      const spend = (domainMax / CURVE_STEPS) * i;
      return {
        spend,
        response: hillSaturation(spend, channel.alpha, channel.gamma, channel.maxObservedSpend) * 100,
      };
    });
  }, [channel]);

  const adstockCurve = useMemo(() => {
    if (!channel?.theta) return [];
    return Array.from({ length: ADSTOCK_MONTHS }, (_, month) => ({
      month,
      carryover: Math.pow(channel.theta as number, month) * 100,
    }));
  }, [channel]);

  const currentResponse =
    channel?.currentSpend !== undefined
      ? hillSaturation(channel.currentSpend, channel.alpha, channel.gamma, channel.maxObservedSpend) * 100
      : undefined;

  const saturationLabel =
    currentResponse === undefined
      ? undefined
      : currentResponse >= 90
        ? 'Maxed out'
        : currentResponse >= 70
          ? 'Approaching saturation'
          : 'Room to grow';

  if (!channel) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-lg font-semibold">Saturation & Diminishing Returns</h3>
        <Select value={channel.channel} onValueChange={setSelected}>
          <SelectTrigger className="w-full sm:w-56">
            <SelectValue placeholder="Select channel" />
          </SelectTrigger>
          <SelectContent>
            {data.map((c) => (
              <SelectItem key={c.channel} value={c.channel}>
                {c.channel}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard
          title={`${channel.channel} — Saturation Curve`}
          tooltip="Robyn's Hill saturation curve: the diminishing-returns response to spend. A flattening curve near the top means additional spend yields little extra return."
          height={280}
        >
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={curve} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="spend" tickFormatter={(v: number) => `₹${(v / 1000).toFixed(0)}k`} />
              <YAxis tickFormatter={(v: number) => `${v.toFixed(0)}%`} domain={[0, 100]} />
              <Tooltip
                formatter={(value: number) => `${value.toFixed(1)}%`}
                labelFormatter={(label: number) =>
                  `Spend: ₹${label.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                }
              />
              <Area type="monotone" dataKey="response" stroke="#38B2AC" fill="#38B2AC33" name="Response" />
              {channel.currentSpend !== undefined && currentResponse !== undefined && (
                <ReferenceDot
                  x={channel.currentSpend}
                  y={currentResponse}
                  r={6}
                  fill="#F6AD55"
                  stroke="none"
                  label={{ value: 'Current spend', position: 'top', fontSize: 12 }}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title={`${channel.channel} — Adstock Carryover`}
          tooltip="Geometric adstock: how much of this month's media effect carries over into future months."
          height={280}
        >
          {adstockCurve.length === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              No adstock decay rate configured for this channel.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={adstockCurve} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" tickFormatter={(v: number) => `+${v}mo`} />
                <YAxis tickFormatter={(v: number) => `${v.toFixed(0)}%`} domain={[0, 100]} />
                <Tooltip
                  formatter={(value: number) => `${value.toFixed(1)}%`}
                  labelFormatter={(label: number) => `${label} month(s) later`}
                />
                <Line type="monotone" dataKey="carryover" stroke="#4FD1C5" dot={false} name="Carryover" />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {saturationLabel && currentResponse !== undefined && (
        <p className="text-sm text-muted-foreground">
          At its current spend level, <strong>{channel.channel}</strong> is capturing{' '}
          <strong>{currentResponse.toFixed(0)}%</strong> of its maximum modeled response —{' '}
          <span className={saturationLabel === 'Maxed out' ? 'font-medium text-destructive' : 'font-medium'}>
            {saturationLabel}
          </span>
          .
        </p>
      )}
    </div>
  );
};
