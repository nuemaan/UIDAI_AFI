import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { ChartCard } from "@/components/dashboard/ChartCard";
import { FrictionBadge } from "@/components/dashboard/FrictionBadge";
import { getDistrictHotspots } from "@/data/mockData";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Search, MapPin, Users, AlertCircle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const DistrictHotspots = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const hotspots = getDistrictHotspots(50);
  
  const filteredHotspots = hotspots.filter(
    d => 
      d.district.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.state.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const chartData = hotspots.slice(0, 15);

  const getBarColor = (afi: number) => {
    if (afi < 50) return "hsl(142, 76%, 36%)";
    if (afi < 100) return "hsl(38, 92%, 50%)";
    return "hsl(0, 72%, 51%)";
  };

  return (
    <DashboardLayout 
      title="District Hotspots" 
      subtitle="Identify where citizens feel the most Aadhaar friction"
    >
      <div className="space-y-6">
        {/* Alert Banner */}
        <div className="flex items-center gap-4 p-4 rounded-lg bg-destructive/10 border border-destructive/30">
          <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
          <div>
            <p className="font-medium text-destructive">High Priority Alert</p>
            <p className="text-sm text-muted-foreground">
              {hotspots.filter(h => h.meanAFI > 100).length} districts are experiencing critical friction levels (AFI &gt; 100)
            </p>
          </div>
        </div>

        {/* Top 15 Chart */}
        <ChartCard
          title="Top 15 Districts by AFI Score"
          subtitle="Districts with highest Aadhaar friction requiring immediate attention"
          caption="These are concrete districts where Aadhaar operations are breaking down. Each requires targeted intervention based on the specific friction type."
        >
          <ResponsiveContainer width="100%" height={450}>
            <BarChart 
              data={chartData} 
              layout="vertical"
              margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
            >
              <XAxis 
                type="number"
                tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 12 }}
                axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                tickLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                label={{ 
                  value: 'AFI Score', 
                  position: 'bottom', 
                  offset: 0,
                  fill: 'hsl(215, 20%, 55%)'
                }}
              />
              <YAxis 
                type="category"
                dataKey="district"
                tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 11 }}
                axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                tickLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                width={90}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(222, 44%, 11%)', 
                  border: '1px solid hsl(217, 33%, 20%)',
                  borderRadius: '8px'
                }}
                labelStyle={{ color: 'hsl(210, 40%, 98%)' }}
                formatter={(value: number, name: string, props: any) => [
                  `${value.toFixed(2)}`,
                  `AFI Score (${props.payload.state})`
                ]}
              />
              <Bar dataKey="meanAFI" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.meanAFI)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Searchable Table */}
        <ChartCard
          title="Complete District Hotspot Table"
          subtitle="Search and explore all high-friction districts"
          actions={
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search district or state..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
          }
        >
          <div className="overflow-x-auto max-h-[500px]">
            <table className="data-table">
              <thead className="sticky top-0 bg-card">
                <tr>
                  <th>Rank</th>
                  <th>District</th>
                  <th>State</th>
                  <th>AFI Score</th>
                  <th>Aadhaar Base</th>
                  <th>Friction Level</th>
                </tr>
              </thead>
              <tbody>
                {filteredHotspots.map((district, index) => (
                  <tr key={`${district.state}-${district.district}`}>
                    <td>
                      <div className="flex items-center justify-center w-7 h-7 rounded-full bg-muted text-xs font-bold">
                        {index + 1}
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{district.district}</span>
                      </div>
                    </td>
                    <td className="text-muted-foreground">{district.state}</td>
                    <td className="font-mono font-semibold">{district.meanAFI.toFixed(2)}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span>{(district.aadhaar_base / 1000000).toFixed(2)}M</span>
                      </div>
                    </td>
                    <td>
                      <FrictionBadge score={district.meanAFI} size="sm" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ChartCard>
      </div>
    </DashboardLayout>
  );
};

export default DistrictHotspots;
