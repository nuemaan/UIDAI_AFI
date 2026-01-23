import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { ChartCard } from "@/components/dashboard/ChartCard";
import { getStateSummary } from "@/data/mockData";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowUp, ArrowDown } from "lucide-react";

const StateComparison = () => {
  const allStates = getStateSummary();
  const [showTop, setShowTop] = useState(true);
  
  const displayStates = showTop 
    ? allStates.slice(0, 10) 
    : allStates.slice(-10).reverse();

  const getBarColor = (afi: number) => {
    if (afi < 50) return "hsl(142, 76%, 36%)";
    if (afi < 80) return "hsl(38, 92%, 50%)";
    return "hsl(0, 72%, 51%)";
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-popover border border-border rounded-lg p-3 shadow-lg">
          <p className="font-semibold">{label}</p>
          <p className="text-sm text-muted-foreground">
            Mean AFI: <span className="font-medium text-foreground">{payload[0].value.toFixed(2)}</span>
          </p>
          <p className="text-sm text-muted-foreground">
            Districts: <span className="font-medium text-foreground">{payload[0].payload.districtCount}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <DashboardLayout 
      title="State-wise AFI Comparison" 
      subtitle="Average Aadhaar Friction Index by state for budget & intervention prioritisation"
    >
      <div className="space-y-6">
        <ChartCard
          title={showTop ? "Top 10 States by Mean AFI (High Friction)" : "Bottom 10 States by Mean AFI (Low Friction)"}
          subtitle="States ranked by average Aadhaar Friction Index"
          caption={showTop 
            ? "These states structurally struggle more with Aadhaar operations — this justifies concentrated policy focus and resource allocation."
            : "These states demonstrate effective Aadhaar operations — their practices could serve as models for high-friction states."
          }
          actions={
            <div className="flex gap-2">
              <Button 
                variant={showTop ? "default" : "outline"} 
                size="sm"
                onClick={() => setShowTop(true)}
                className="gap-2"
              >
                <ArrowUp className="h-4 w-4" />
                Top 10
              </Button>
              <Button 
                variant={!showTop ? "default" : "outline"} 
                size="sm"
                onClick={() => setShowTop(false)}
                className="gap-2"
              >
                <ArrowDown className="h-4 w-4" />
                Bottom 10
              </Button>
            </div>
          }
        >
          <ResponsiveContainer width="100%" height={400}>
            <BarChart 
              data={displayStates} 
              layout="vertical"
              margin={{ top: 20, right: 30, left: 120, bottom: 20 }}
            >
              <XAxis 
                type="number"
                tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 12 }}
                axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                tickLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                label={{ 
                  value: 'Mean AFI Score', 
                  position: 'bottom', 
                  offset: 0,
                  fill: 'hsl(215, 20%, 55%)'
                }}
              />
              <YAxis 
                type="category"
                dataKey="state"
                tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 12 }}
                axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                tickLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                width={110}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="meanAFI" 
                radius={[0, 4, 4, 0]}
              >
                {displayStates.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.meanAFI)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* State Table */}
        <ChartCard
          title="All States Overview"
          subtitle="Complete state-wise breakdown"
        >
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>State</th>
                  <th>Mean AFI</th>
                  <th>District Observations</th>
                  <th>Friction Level</th>
                </tr>
              </thead>
              <tbody>
                {allStates.slice(0, 15).map((state, index) => (
                  <tr key={state.state}>
                    <td className="font-medium">{index + 1}</td>
                    <td className="font-medium">{state.state}</td>
                    <td>{state.meanAFI.toFixed(2)}</td>
                    <td>{state.districtCount}</td>
                    <td>
                      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                        state.meanAFI < 50 
                          ? 'friction-low' 
                          : state.meanAFI < 80 
                            ? 'friction-medium' 
                            : 'friction-high'
                      }`}>
                        {state.meanAFI < 50 ? 'Low' : state.meanAFI < 80 ? 'Medium' : 'High'}
                      </span>
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

export default StateComparison;
