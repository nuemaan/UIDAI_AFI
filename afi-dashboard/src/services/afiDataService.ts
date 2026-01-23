import { supabase } from "@/integrations/supabase/client";

export interface DistrictData {
  id: string;
  period: string;
  state_canonical: string;
  district_clean: string;
  pincode: string | null;
  afi_composite_score: number;
  enrol_total: number | null;
  demo_total: number | null;
  bio_total: number | null;
  aadhaar_base: number | null;
  age_mismatch_score: number | null;
  cluster_id?: number | null;
  cluster_name?: string | null;
}

// Fetch all district data from database
export const fetchDistrictData = async (): Promise<DistrictData[]> => {
  const { data, error } = await supabase
    .from("district_afi_data")
    .select("*")
    .order("afi_composite_score", { ascending: false });

  if (error) {
    console.error("Error fetching district data:", error);
    throw error;
  }

  return data || [];
};

// Get state summary with mean AFI
export const getStateSummary = (data: DistrictData[]) => {
  const stateMap = new Map<string, { total: number; count: number }>();

  data.forEach((d) => {
    const existing = stateMap.get(d.state_canonical) || { total: 0, count: 0 };
    stateMap.set(d.state_canonical, {
      total: existing.total + d.afi_composite_score,
      count: existing.count + 1,
    });
  });

  return Array.from(stateMap.entries())
    .map(([state, { total, count }]) => ({
      state,
      meanAFI: Math.round((total / count) * 100) / 100,
      districtCount: count,
    }))
    .sort((a, b) => b.meanAFI - a.meanAFI);
};

// Get typology summary
export const getTypologySummary = (data: DistrictData[]) => {
  const typologyMap = new Map<string, number>();

  data.forEach((d) => {
    if (d.cluster_name) {
      typologyMap.set(d.cluster_name, (typologyMap.get(d.cluster_name) || 0) + 1);
    }
  });

  return Array.from(typologyMap.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);
};

// Get district hotspots
export const getDistrictHotspots = (data: DistrictData[], limit = 15) => {
  const districtMap = new Map<
    string,
    {
      state: string;
      district: string;
      totalAFI: number;
      count: number;
      aadhaar_base: number | null;
    }
  >();

  data.forEach((d) => {
    const key = `${d.state_canonical}-${d.district_clean}`;
    const existing = districtMap.get(key) || {
      state: d.state_canonical,
      district: d.district_clean,
      totalAFI: 0,
      count: 0,
      aadhaar_base: d.aadhaar_base,
    };
    districtMap.set(key, {
      ...existing,
      totalAFI: existing.totalAFI + d.afi_composite_score,
      count: existing.count + 1,
    });
  });

  return Array.from(districtMap.values())
    .map((d) => ({
      state: d.state,
      district: d.district,
      meanAFI: Math.round((d.totalAFI / d.count) * 100) / 100,
      aadhaar_base: d.aadhaar_base,
    }))
    .sort((a, b) => b.meanAFI - a.meanAFI)
    .slice(0, limit);
};

// Get AFI distribution
export const getAFIDistribution = (data: DistrictData[]) => {
  const buckets = [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200];
  const distribution = buckets.slice(0, -1).map((min, i) => ({
    range: `${min}-${buckets[i + 1]}`,
    count: 0,
    min,
    max: buckets[i + 1],
  }));

  data.forEach((d) => {
    const bucket = distribution.find(
      (b) => d.afi_composite_score >= b.min && d.afi_composite_score < b.max
    );
    if (bucket) bucket.count++;
  });

  const overflowCount = data.filter((d) => d.afi_composite_score >= 200).length;
  if (overflowCount > 0) {
    distribution.push({ range: "200+", count: overflowCount, min: 200, max: 999 });
  }

  return distribution;
};

// Get national stats
export const getNationalStats = (data: DistrictData[]) => {
  if (data.length === 0) {
    return {
      median: 0,
      p95: 0,
      p99: 0,
      min: 0,
      max: 0,
      totalDistricts: 0,
      highFrictionDistricts: 0,
    };
  }

  const scores = data.map((d) => d.afi_composite_score).sort((a, b) => a - b);
  const n = scores.length;

  return {
    median: scores[Math.floor(n / 2)],
    p95: scores[Math.floor(n * 0.95)],
    p99: scores[Math.floor(n * 0.99)],
    min: scores[0],
    max: scores[n - 1],
    totalDistricts: new Set(
      data.map((d) => `${d.state_canonical}-${d.district_clean}`)
    ).size,
    highFrictionDistricts: new Set(
      data
        .filter((d) => d.afi_composite_score > scores[Math.floor(n * 0.9)])
        .map((d) => `${d.state_canonical}-${d.district_clean}`)
    ).size,
  };
};

// Get decomposition data
export const getDecompositionData = (data: DistrictData[]) => {
  return data
    .filter((_, i) => i % 6 === 0)
    .map((d) => ({
      district: d.district_clean,
      state: d.state_canonical,
      afi: d.afi_composite_score,
      bio_intensity: d.bio_total && d.aadhaar_base 
        ? (d.bio_total / d.aadhaar_base) * 1000 
        : 0,
      demo_pressure: d.demo_total && d.aadhaar_base 
        ? (d.demo_total / d.aadhaar_base) * 1000 
        : 0,
      age_mismatch: d.age_mismatch_score || 0,
      aadhaar_base: d.aadhaar_base || 0,
    }));
};

// Get state typology matrix
export const getStateTypologyMatrix = (data: DistrictData[]) => {
  const matrix = new Map<string, Map<string, number>>();

  data.forEach((d) => {
    if (!d.cluster_name) return;

    if (!matrix.has(d.state_canonical)) {
      matrix.set(d.state_canonical, new Map());
    }
    const stateMap = matrix.get(d.state_canonical)!;
    stateMap.set(d.cluster_name, (stateMap.get(d.cluster_name) || 0) + 1);
  });

  const stateTotals = Array.from(matrix.entries())
    .map(([state, typMap]) => ({
      state,
      total: Array.from(typMap.values()).reduce((a, b) => a + b, 0),
    }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 10);

  return stateTotals.map(({ state }) => {
    const typMap = matrix.get(state)!;
    return {
      state,
      "Biometric-Stress Districts": typMap.get("Biometric-Stress Districts") || 0,
      "Documentation-Heavy Districts": typMap.get("Documentation-Heavy Districts") || 0,
      "Transition-Backlog Districts": typMap.get("Transition-Backlog Districts") || 0,
      "Low-Friction Stable Districts": typMap.get("Low-Friction Stable Districts") || 0,
      "High-Volume Urban Districts": typMap.get("High-Volume Urban Districts") || 0,
    };
  });
};

// Upload CSV data to database
export const uploadCSVData = async (
  records: Array<{
    period: string;
    state_canonical: string;
    district_clean: string;
    pincode?: string;
    afi_composite_score: number;
    enrol_total?: number;
    demo_total?: number;
    bio_total?: number;
    aadhaar_base?: number;
    age_mismatch_score?: number;
    cluster_id?: number;
    cluster_name?: string;
  }>,
  onProgress?: (progress: number) => void
) => {
  // Delete existing data first
  const { error: deleteError } = await supabase
    .from("district_afi_data")
    .delete()
    .neq("id", "00000000-0000-0000-0000-000000000000"); // Delete all rows

  if (deleteError) {
    console.error("Error deleting existing data:", deleteError);
    throw deleteError;
  }

  onProgress?.(5);

  // Insert new data in batches of 1000
  const batchSize = 1000;
  const batches: Array<typeof records> = [];
  
  for (let i = 0; i < records.length; i += batchSize) {
    batches.push(records.slice(i, i + batchSize));
  }

  const totalBatches = batches.length;
  let completedBatches = 0;

  // Process batches in parallel groups of 5 for speed
  const parallelBatches = 5;
  for (let i = 0; i < batches.length; i += parallelBatches) {
    const batchGroup = batches.slice(i, i + parallelBatches);
    
    const results = await Promise.all(
      batchGroup.map(batch => 
        supabase.from("district_afi_data").insert(batch)
      )
    );

    // Check for errors
    for (const { error } of results) {
      if (error) {
        console.error("Error inserting data:", error);
        throw error;
      }
    }

    completedBatches += batchGroup.length;
    const progress = Math.round((completedBatches / totalBatches) * 95) + 5;
    onProgress?.(progress);
  }

  return { success: true, count: records.length };
};
