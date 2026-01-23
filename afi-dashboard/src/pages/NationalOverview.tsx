import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { StatCard } from "@/components/dashboard/StatCard";
import { ChartCard } from "@/components/dashboard/ChartCard";
import { getNationalStats, getAFIDistribution, getDistrictHotspots } from "@/data/mockData";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";
import { Activity, AlertTriangle, MapPin, TrendingUp } from "lucide-react";
import { FrictionBadge } from "@/components/dashboard/FrictionBadge";

const NationalOverview = () => {
  const stats = getNationalStats();
  const distribution = getAFIDistribution();
  const hotspots = getDistrictHotspots(5);

  const getBarColor = (range: string) => {
    const value = parseInt(range.split("-")[0]);
    if (value < 50) return "hsl(142, 76%, 36%)";
    if (value < 100) return "hsl(38, 92%, 50%)";
    return "hsl(0, 72%, 51%)";
  };

  return (
    <DashboardLayout 
      title="National AFI Overview" 
      subtitle="Distribution of Aadhaar Friction Index across India"
    >
      <div className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Districts Monitored"
            value={stats.totalDistricts.toLocaleString()}
            subtitle="Across all states"
            icon={MapPin}
            variant="default"
          />
          <StatCard
            title="High Friction Districts"
            value={stats.highFrictionDistricts}
            subtitle="Above 90th percentile"
            icon={AlertTriangle}
            variant="destructive"
            trend={{ value: 12, label: "vs last quarter" }}
          />
          <StatCard
            title="Median AFI Score"
            value={stats.median.toFixed(1)}
            subtitle="National median"
            icon={Activity}
            variant="primary"
          />
          <StatCard
            title="95th Percentile"
            value={stats.p95.toFixed(1)}
            subtitle="Extreme friction threshold"
            icon={TrendingUp}
            variant="warning"
          />
        </div>

        {/* Distribution Chart */}
        <ChartCard
          title="Distribution of Aadhaar Friction Index Across India"
          subtitle="District-month observations by AFI score range"
          caption="Most districts experience low Aadhaar friction, while a small number face extremely high friction. This long tail indicates that Aadhaar-related difficulties are highly localized rather than nationwide, supporting targeted district-level policy interventions."
        >
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={distribution} margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
              <XAxis 
                dataKey="range" 
                tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 12 }}
                axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                tickLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                label={{ 
                  value: 'AFI Score Range', 
                  position: 'bottom', 
                  offset: 20,
                  fill: 'hsl(215, 20%, 55%)'
                }}
              />
              <YAxis 
                tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 12 }}
                axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                tickLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                label={{ 
                  value: 'District-Month Count', 
                  angle: -90, 
                  position: 'insideLeft',
                  fill: 'hsl(215, 20%, 55%)'
                }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(222, 44%, 11%)', 
                  border: '1px solid hsl(217, 33%, 20%)',
                  borderRadius: '8px'
                }}
                labelStyle={{ color: 'hsl(210, 40%, 98%)' }}
                itemStyle={{ color: 'hsl(210, 40%, 98%)' }}
              />
              <ReferenceLine 
                x={`${Math.floor(stats.median / 20) * 20}-${Math.floor(stats.median / 20) * 20 + 20}`}
                stroke="hsl(24, 95%, 53%)"
                strokeDasharray="5 5"
                label={{ value: 'Median', fill: 'hsl(24, 95%, 53%)', fontSize: 11 }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.range)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Quick Hotspots Preview */}
        <ChartCard
          title="Top 5 High-Friction Districts"
          subtitle="Districts requiring immediate policy attention"
        >
          <div className="space-y-4">
            {hotspots.map((district, index) => (
              <div 
                key={`${district.state}-${district.district}`}
                className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border hover:border-primary/30 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-destructive/20 text-destructive font-bold text-sm">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium">{district.district}</p>
                    <p className="text-sm text-muted-foreground">{district.state}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Aadhaar Base</p>
                    <p className="text-sm font-medium">{(district.aadhaar_base / 1000000).toFixed(2)}M</p>
                  </div>
                  <FrictionBadge score={district.meanAFI} />
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>
    </DashboardLayout>
  );
};

export default NationalOverview;
