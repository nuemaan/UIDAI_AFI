import { Database, Beaker } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useAFIData } from "@/hooks/useAFIData";

const DataSourceBadge = () => {
  const { dataSource, hasRealData, rawData } = useAFIData();

  if (hasRealData) {
    return (
      <Badge variant="outline" className="gap-1 border-green-500/50 text-green-600">
        <Database className="h-3 w-3" />
        Live Data ({rawData.length} records)
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="gap-1 border-amber-500/50 text-amber-600">
      <Beaker className="h-3 w-3" />
      Mock Data
    </Badge>
  );
};

export default DataSourceBadge;
