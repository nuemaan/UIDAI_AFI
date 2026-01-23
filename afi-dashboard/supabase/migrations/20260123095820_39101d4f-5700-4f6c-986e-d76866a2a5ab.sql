-- Create table for district-level AFI data (matches merged_for_afi.csv structure)
CREATE TABLE public.district_afi_data (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  period TEXT NOT NULL,
  state_canonical TEXT NOT NULL,
  district_clean TEXT NOT NULL,
  pincode TEXT,
  afi_composite_score NUMERIC NOT NULL,
  enrol_total INTEGER,
  demo_total INTEGER,
  bio_total INTEGER,
  aadhaar_base INTEGER,
  age_mismatch_score NUMERIC,
  cluster_id INTEGER,
  cluster_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.district_afi_data ENABLE ROW LEVEL SECURITY;

-- Create policy for public read access (dashboard is public)
CREATE POLICY "Anyone can read district AFI data"
ON public.district_afi_data
FOR SELECT
USING (true);

-- Create policy for authenticated users to insert data (admin upload)
CREATE POLICY "Authenticated users can insert AFI data"
ON public.district_afi_data
FOR INSERT
WITH CHECK (auth.uid() IS NOT NULL);

-- Create policy for authenticated users to delete data (for re-uploads)
CREATE POLICY "Authenticated users can delete AFI data"
ON public.district_afi_data
FOR DELETE
USING (auth.uid() IS NOT NULL);

-- Create index for common queries
CREATE INDEX idx_district_afi_state ON public.district_afi_data(state_canonical);
CREATE INDEX idx_district_afi_period ON public.district_afi_data(period);
CREATE INDEX idx_district_afi_score ON public.district_afi_data(afi_composite_score DESC);