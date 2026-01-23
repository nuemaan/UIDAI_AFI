import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { ChartCard } from "@/components/dashboard/ChartCard";
import { StatCard } from "@/components/dashboard/StatCard";
import { getTypologySummary, getStateTypologyMatrix } from "@/data/mockData";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend, PieChart, Pie } from "recharts";
import { Brain, Layers, Target, TrendingDown } from "lucide-react";

const TYPOLOGY_COLORS: Record<string, string> = {
  "Biometric-Stress Districts": "hsl(0, 72%, 51%)",
  "Documentation-Heavy Districts": "hsl(38, 92%, 50%)",
  "Transition-Backlog Districts": "hsl(262, 83%, 58%)",
  "Low-Friction Stable Districts": "hsl(142, 76%, 36%)",
  "High-Volume Urban Districts": "hsl(217, 91%, 60%)",
};

const TYPOLOGY_DESCRIPTIONS: Record<string, string> = {
  "Biometric-Stress Districts": "High biometric update demand - need equipment upgrades and more operators",
  "Documentation-Heavy Districts": "High demographic correction rates - may indicate data quality issues at enrolment",
  "Transition-Backlog Districts": "Age-related update backlogs - need school-based update camps",
  "Low-Friction Stable Districts": "Well-functioning Aadhaar ecosystem - best practices to be studied",
  "High-Volume Urban Districts": "High volume with moderate friction - capacity scaling needed",
};

const DistrictTypologies = () => {
  const typologyData = getTypologySummary();
  const matrixData = getStateTypologyMatrix();

  const totalObservations = typologyData.reduce((sum, t) => sum + t.count, 0);

  const pieData = typologyData.map(t => ({
    name: t.name,
    value: t.count,
    percentage: ((t.count / totalObservations) * 100).toFixed(1)
  }));

  return (
    <DashboardLayout 
      title="District Typologies" 
      subtitle="AI-driven classification for actionable policy interventions"
    >
      <div className="space-y-6">
        {/* Info Banner */}
        <div className="flex items-start gap-4 p-5 rounded-lg bg-primary/10 border border-primary/30">
          <Brain className="h-6 w-6 text-primary shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-primary">Unsupervised AI Clustering</p>
            <p className="text-sm text-muted-foreground mt-1">
              Districts are automatically grouped based on similar Aadhaar enrolment and update patterns using machine learning.
              This moves policymaking from simple ranking to <strong>actionable intervention types</strong> — 
              different districts need different solutions.
            </p>
          </div>
        </div>

        {/* Typology Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {typologyData.map((typology, index) => (
            <StatCard
              key={typology.name}
              title={typology.name.replace(" Districts", "")}
              value={typology.count}
              subtitle={`${((typology.count / totalObservations) * 100).toFixed(1)}% of observations`}
              icon={index === 0 ? Target : index === 1 ? Layers : index === 2 ? TrendingDown : Target}
              variant={
                typology.name.includes("Biometric") ? "destructive" :
                typology.name.includes("Documentation") ? "warning" :
                typology.name.includes("Low-Friction") ? "success" : "default"
              }
            />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Typology Size Chart */}
          <ChartCard
            title="District Typologies by Size"
            subtitle="Count of district-month observations per typology"
            caption="Each typology groups districts with similar Aadhaar enrolment and update behaviour. Larger segments indicate patterns that are widespread across India."
          >
            <ResponsiveContainer width="100%" height={350}>
              <BarChart 
                data={typologyData} 
                margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
              >
                <XAxis 
                  dataKey="name"
                  tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 10 }}
                  axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                  tickLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                  angle={-25}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 12 }}
                  axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(222, 44%, 11%)', 
                    border: '1px solid hsl(217, 33%, 20%)',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: 'hsl(210, 40%, 98%)' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {typologyData.map((entry) => (
                    <Cell key={entry.name} fill={TYPOLOGY_COLORS[entry.name] || "hsl(217, 91%, 60%)"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Pie Chart */}
          <ChartCard
            title="Typology Distribution"
            subtitle="Proportion of each district type"
          >
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percentage }) => `${percentage}%`}
                  labelLine={{ stroke: 'hsl(215, 20%, 55%)' }}
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={TYPOLOGY_COLORS[entry.name] || "hsl(217, 91%, 60%)"} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(222, 44%, 11%)', 
                    border: '1px solid hsl(217, 33%, 20%)',
                    borderRadius: '8px'
                  }}
                  formatter={(value: number, name: string) => [value, name]}
                />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Typology Descriptions */}
        <ChartCard
          title="Typology Descriptions & Recommended Interventions"
          subtitle="What each classification means for policy action"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(TYPOLOGY_DESCRIPTIONS).map(([name, description]) => (
              <div 
                key={name}
                className="p-4 rounded-lg border border-border bg-muted/20 hover:border-primary/30 transition-colors"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: TYPOLOGY_COLORS[name] }}
                  />
                  <h4 className="font-medium text-sm">{name}</h4>
                </div>
                <p className="text-sm text-muted-foreground">{description}</p>
              </div>
            ))}
          </div>
        </ChartCard>

        {/* State × Typology Matrix */}
        <ChartCard
          title="State × Typology Composition"
          subtitle="Top 10 states by observation volume - typology mix breakdown"
          caption="This matrix reveals how friction types vary across states. Some states may have concentrated typologies, while others show diverse friction patterns requiring multi-pronged interventions."
        >
          <ResponsiveContainer width="100%" height={400}>
            <BarChart 
              data={matrixData} 
              layout="vertical"
              margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
            >
              <XAxis 
                type="number"
                tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 12 }}
                axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
              />
              <YAxis 
                type="category"
                dataKey="state"
                tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 11 }}
                axisLine={{ stroke: 'hsl(217, 33%, 20%)' }}
                width={95}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(222, 44%, 11%)', 
                  border: '1px solid hsl(217, 33%, 20%)',
                  borderRadius: '8px'
                }}
              />
              <Legend wrapperStyle={{ paddingTop: 20 }} />
              {Object.keys(TYPOLOGY_COLORS).map((typology) => (
                <Bar 
                  key={typology}
                  dataKey={typology}
                  stackId="a"
                  fill={TYPOLOGY_COLORS[typology]}
                  name={typology.replace(" Districts", "")}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </DashboardLayout>
  );
};

export default DistrictTypologies;
