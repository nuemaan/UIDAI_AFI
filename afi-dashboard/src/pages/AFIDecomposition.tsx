import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { ChartCard } from "@/components/dashboard/ChartCard";
import { getDecompositionData } from "@/data/mockData";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, ZAxis, Cell } from "recharts";
import { Info } from "lucide-react";

const AFIDecomposition = () => {
  const decompositionData = getDecompositionData();

  const getPointColor = (afi: number) => {
    if (afi < 50) return "hsl(142, 76%, 36%)";
    if (afi < 100) return "hsl(38, 92%, 50%)";
    return "hsl(0, 72%, 51%)";
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-popover border border-border rounded-lg p-4 shadow-lg max-w-xs">
          <p className="font-semibold">{data.district}</p>
          <p className="text-sm text-muted-foreground mb-2">{data.state}</p>
          <div className="space-y-1 text-sm">
            <p>AFI Score: <span className="font-medium">{data.afi.toFixed(2)}</span></p>
            <p>Biometric Intensity: <span className="font-medium">{data.bio_intensity.toFixed(3)}</span></p>
            <p>Demo Pressure: <span className="font-medium">{data.demo_pressure.toFixed(3)}</span></p>
            <p>Age Mismatch: <span className="font-medium">{data.age_mismatch.toFixed(2)}</span></p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <DashboardLayout 
      title="AFI Decomposition" 
      subtitle="Understand why specific districts have high friction"
    >
      <div className="space-y-6">
        {/* Explanation Card */}
        <div className="flex items-start gap-4 p-5 rounded-lg bg-info/10 border border-info/30">
          <Info className="h-5 w-5 text-info shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-info">Understanding AFI Components</p>
            <p className="text-sm text-muted-foreground mt-1">
              The AFI is composed of three key drivers: <strong>Biometric Update Intensity</strong> (fingerprint/iris updates per capita), 
              <strong> Demographic Correction Pressure</strong> (name/address changes per capita), and 
              <strong> Age-Transition Mismatch Score</strong> (delays in mandatory updates for 5-15 year olds).
              This prevents the "black box index" problem.
            </p>
          </div>
        </div>

        {/* Biometric vs AFI */}
        <ChartCard
          title="Biometric Update Intensity vs AFI Score"
          subtitle="Higher biometric update rates often correlate with citizen friction"
          caption="Districts in the upper-right quadrant face dual pressure: high AFI and high biometric update demand. These may need additional enrolment centers or improved biometric capture equipment."
        >
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
              <XAxis 
                type="number"
                dataKey="bio_intensity"
                name="Biometric Intensity"
                tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 12 }}
                axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                tickLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                label={{ 
                  value: 'Biometric Update Intensity (per 1000 Aadhaar)', 
                  position: 'bottom', 
                  offset: 20,
                  fill: 'hsl(215, 20%, 55%)'
                }}
              />
              <YAxis 
                type="number"
                dataKey="afi"
                name="AFI Score"
                tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 12 }}
                axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                tickLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                label={{ 
                  value: 'AFI Score', 
                  angle: -90, 
                  position: 'insideLeft',
                  fill: 'hsl(215, 20%, 55%)'
                }}
              />
              <ZAxis type="number" dataKey="aadhaar_base" range={[30, 200]} />
              <Tooltip content={<CustomTooltip />} />
              <Scatter data={decompositionData}>
                {decompositionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getPointColor(entry.afi)} fillOpacity={0.7} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </ChartCard>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Demo Pressure vs AFI */}
          <ChartCard
            title="Demographic Pressure vs AFI"
            subtitle="Name/address correction demand"
          >
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ top: 20, right: 20, left: 20, bottom: 40 }}>
                <XAxis 
                  type="number"
                  dataKey="demo_pressure"
                  tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 11 }}
                  axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                  label={{ 
                    value: 'Demo Pressure (per 1000)', 
                    position: 'bottom', 
                    offset: 20,
                    fill: 'hsl(215, 20%, 55%)',
                    fontSize: 11
                  }}
                />
                <YAxis 
                  type="number"
                  dataKey="afi"
                  tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 11 }}
                  axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Scatter data={decompositionData}>
                  {decompositionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getPointColor(entry.afi)} fillOpacity={0.7} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Age Mismatch vs AFI */}
          <ChartCard
            title="Age Mismatch Score vs AFI"
            subtitle="Child/adolescent update backlogs"
          >
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ top: 20, right: 20, left: 20, bottom: 40 }}>
                <XAxis 
                  type="number"
                  dataKey="age_mismatch"
                  tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 11 }}
                  axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                  label={{ 
                    value: 'Age Mismatch Score', 
                    position: 'bottom', 
                    offset: 20,
                    fill: 'hsl(215, 20%, 55%)',
                    fontSize: 11
                  }}
                />
                <YAxis 
                  type="number"
                  dataKey="afi"
                  tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 11 }}
                  axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Scatter data={decompositionData}>
                  {decompositionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getPointColor(entry.afi)} fillOpacity={0.7} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-8 p-4 rounded-lg bg-muted/30">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-success" />
            <span className="text-sm text-muted-foreground">Low Friction (&lt;50)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-warning" />
            <span className="text-sm text-muted-foreground">Medium Friction (50-100)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-destructive" />
            <span className="text-sm text-muted-foreground">High Friction (&gt;100)</span>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AFIDecomposition;
