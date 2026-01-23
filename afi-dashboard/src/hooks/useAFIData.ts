import { useQuery } from "@tanstack/react-query";
import {
  fetchDistrictData,
  getStateSummary,
  getTypologySummary,
  getDistrictHotspots,
  getAFIDistribution,
  getNationalStats,
  getDecompositionData,
  getStateTypologyMatrix,
  DistrictData,
} from "@/services/afiDataService";
import {
  mockDistrictData,
  getStateSummary as getMockStateSummary,
  getTypologySummary as getMockTypologySummary,
  getDistrictHotspots as getMockDistrictHotspots,
  getAFIDistribution as getMockAFIDistribution,
  getNationalStats as getMockNationalStats,
  getDecompositionData as getMockDecompositionData,
  getStateTypologyMatrix as getMockStateTypologyMatrix,
} from "@/data/mockData";

export const useAFIData = () => {
  const {
    data: dbData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["district-afi-data"],
    queryFn: fetchDistrictData,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Use database data if available, otherwise fall back to mock data
  const hasRealData = dbData && dbData.length > 0;
  
  const rawData: DistrictData[] = hasRealData
    ? dbData
    : mockDistrictData.map((d, i) => ({
        ...d,
        id: `mock-${i}`,
      }));

  return {
    rawData,
    isLoading,
    error,
    refetch,
    hasRealData,
    dataSource: hasRealData ? "database" : "mock",
    
    // Computed data
    stateSummary: hasRealData ? getStateSummary(rawData) : getMockStateSummary(),
    typologySummary: hasRealData ? getTypologySummary(rawData) : getMockTypologySummary(),
    districtHotspots: (limit?: number) =>
      hasRealData
        ? getDistrictHotspots(rawData, limit)
        : getMockDistrictHotspots(limit),
    afiDistribution: hasRealData ? getAFIDistribution(rawData) : getMockAFIDistribution(),
    nationalStats: hasRealData ? getNationalStats(rawData) : getMockNationalStats(),
    decompositionData: hasRealData ? getDecompositionData(rawData) : getMockDecompositionData(),
    stateTypologyMatrix: hasRealData
      ? getStateTypologyMatrix(rawData)
      : getMockStateTypologyMatrix(),
  };
};
