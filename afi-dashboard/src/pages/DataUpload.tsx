import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Papa from "papaparse";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Upload, FileText, CheckCircle2, AlertCircle, LogIn, LogOut } from "lucide-react";
import { uploadCSVData } from "@/services/afiDataService";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { useQueryClient } from "@tanstack/react-query";

interface ParsedRow {
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
}

const REQUIRED_COLUMNS = [
  "period",
  "state_canonical",
  "district_clean",
  "afi_composite_score",
];

const DataUpload = () => {
  const { user, signIn, signUp, signOut, isLoading: authLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  
  const [file, setFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<ParsedRow[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  
  const { toast } = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    
    const { error } = isSignUp 
      ? await signUp(email, password)
      : await signIn(email, password);
    
    if (error) {
      setAuthError(error.message);
    } else {
      toast({
        title: isSignUp ? "Account created!" : "Signed in!",
        description: isSignUp 
          ? "You can now upload CSV data." 
          : "Welcome back!",
      });
    }
  };

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setParseError(null);
    setParsedData([]);
    setUploadSuccess(false);

    Papa.parse<Record<string, string>>(selectedFile, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const headers = results.meta.fields || [];
        
        // Check for required columns
        const missingColumns = REQUIRED_COLUMNS.filter(
          (col) => !headers.includes(col)
        );
        
        if (missingColumns.length > 0) {
          setParseError(
            `Missing required columns: ${missingColumns.join(", ")}`
          );
          return;
        }

        // Parse and validate data
        const parsed: ParsedRow[] = results.data
          .filter((row) => row.period && row.state_canonical && row.district_clean)
          .map((row) => ({
            period: row.period,
            state_canonical: row.state_canonical,
            district_clean: row.district_clean,
            pincode: row.pincode || undefined,
            afi_composite_score: parseFloat(row.afi_composite_score) || 0,
            enrol_total: row.enrol_total ? parseInt(row.enrol_total) : undefined,
            demo_total: row.demo_total ? parseInt(row.demo_total) : undefined,
            bio_total: row.bio_total ? parseInt(row.bio_total) : undefined,
            aadhaar_base: row.aadhaar_base ? parseInt(row.aadhaar_base) : undefined,
            age_mismatch_score: row.age_mismatch_score
              ? parseFloat(row.age_mismatch_score)
              : undefined,
            cluster_id: row.cluster_id ? parseInt(row.cluster_id) : undefined,
            cluster_name: row.cluster_name || undefined,
          }));

        if (parsed.length === 0) {
          setParseError("No valid data rows found in the CSV file.");
          return;
        }

        setParsedData(parsed);
        toast({
          title: "CSV parsed successfully!",
          description: `Found ${parsed.length} valid records.`,
        });
      },
      error: (error) => {
        setParseError(`Failed to parse CSV: ${error.message}`);
      },
    });
  }, [toast]);

  const handleUpload = async () => {
    if (parsedData.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);
    setParseError(null);

    try {
      await uploadCSVData(parsedData, (progress) => {
        setUploadProgress(progress);
      });

      setUploadProgress(100);
      setUploadSuccess(true);
      
      // Invalidate and refetch the data
      await queryClient.invalidateQueries({ queryKey: ["district-afi-data"] });

      toast({
        title: "Upload successful!",
        description: `${parsedData.length} records uploaded to the database.`,
      });

      // Reset after success
      setTimeout(() => {
        setFile(null);
        setParsedData([]);
        setUploadProgress(0);
      }, 2000);
    } catch (error) {
      console.error("Upload error:", error);
      setParseError(`Upload failed: ${(error as Error).message}`);
      setUploadProgress(0);
    } finally {
      setIsUploading(false);
    }
  };

  if (authLoading) {
    return (
      <DashboardLayout title="Data Upload" subtitle="Loading...">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Data Upload" subtitle="Upload your AFI CSV files">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Data Upload</h1>
          <p className="text-muted-foreground mt-1">
            Upload your AFI CSV files to replace mock data with real data
          </p>
        </div>

        {!user ? (
          <Card className="max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LogIn className="h-5 w-5" />
                {isSignUp ? "Create Account" : "Sign In"}
              </CardTitle>
              <CardDescription>
                You need to sign in to upload CSV data
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAuth} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="admin@example.com"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                  />
                </div>
                {authError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{authError}</AlertDescription>
                  </Alert>
                )}
                <Button type="submit" className="w-full">
                  {isSignUp ? "Create Account" : "Sign In"}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  className="w-full"
                  onClick={() => setIsSignUp(!isSignUp)}
                >
                  {isSignUp
                    ? "Already have an account? Sign in"
                    : "Need an account? Sign up"}
                </Button>
              </form>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Signed in as <span className="font-medium">{user.email}</span>
              </p>
              <Button variant="outline" size="sm" onClick={signOut}>
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              {/* Upload Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="h-5 w-5" />
                    Upload CSV
                  </CardTitle>
                  <CardDescription>
                    Select a CSV file matching the AFI data schema
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="csv-file">CSV File</Label>
                    <Input
                      id="csv-file"
                      type="file"
                      accept=".csv"
                      onChange={handleFileChange}
                      disabled={isUploading}
                    />
                  </div>

                  {file && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <FileText className="h-4 w-4" />
                      {file.name} ({(file.size / 1024).toFixed(1)} KB)
                    </div>
                  )}

                  {parseError && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>Parse Error</AlertTitle>
                      <AlertDescription>{parseError}</AlertDescription>
                    </Alert>
                  )}

                  {parsedData.length > 0 && !uploadSuccess && (
                    <Alert>
                      <CheckCircle2 className="h-4 w-4" />
                      <AlertTitle>Ready to Upload</AlertTitle>
                      <AlertDescription>
                        {parsedData.length} records parsed successfully.
                        Click Upload to save to database.
                      </AlertDescription>
                    </Alert>
                  )}

                  {uploadSuccess && (
                    <Alert className="border-green-500 bg-green-500/10">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <AlertTitle className="text-green-500">Success!</AlertTitle>
                      <AlertDescription>
                        Data uploaded successfully. Dashboard now shows real data.
                      </AlertDescription>
                    </Alert>
                  )}

                  {isUploading && (
                    <div className="space-y-2">
                      <Progress value={uploadProgress} />
                      <p className="text-sm text-muted-foreground text-center">
                        Uploading... {uploadProgress}%
                      </p>
                    </div>
                  )}

                  <Button
                    onClick={handleUpload}
                    disabled={parsedData.length === 0 || isUploading}
                    className="w-full"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Upload {parsedData.length} Records
                  </Button>
                </CardContent>
              </Card>

              {/* Schema Info Card */}
              <Card>
                <CardHeader>
                  <CardTitle>Expected CSV Schema</CardTitle>
                  <CardDescription>
                    Your CSV should have these columns
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="font-medium text-destructive">Required:</p>
                      <ul className="list-disc list-inside text-muted-foreground">
                        <li>period (e.g., "2024-01")</li>
                        <li>state_canonical</li>
                        <li>district_clean</li>
                        <li>afi_composite_score (numeric)</li>
                      </ul>
                    </div>
                    <div>
                      <p className="font-medium text-muted-foreground">Optional:</p>
                      <ul className="list-disc list-inside text-muted-foreground">
                        <li>pincode</li>
                        <li>enrol_total, demo_total, bio_total</li>
                        <li>aadhaar_base</li>
                        <li>age_mismatch_score</li>
                        <li>cluster_id, cluster_name (for typologies)</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Preview Table */}
            {parsedData.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Data Preview (First 10 rows)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">Period</th>
                          <th className="text-left p-2">State</th>
                          <th className="text-left p-2">District</th>
                          <th className="text-right p-2">AFI Score</th>
                          <th className="text-left p-2">Typology</th>
                        </tr>
                      </thead>
                      <tbody>
                        {parsedData.slice(0, 10).map((row, i) => (
                          <tr key={i} className="border-b border-border/50">
                            <td className="p-2">{row.period}</td>
                            <td className="p-2">{row.state_canonical}</td>
                            <td className="p-2">{row.district_clean}</td>
                            <td className="p-2 text-right font-mono">
                              {row.afi_composite_score.toFixed(2)}
                            </td>
                            <td className="p-2 text-muted-foreground">
                              {row.cluster_name || "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            <Button variant="outline" onClick={() => navigate("/")}>
              ← Back to Dashboard
            </Button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default DataUpload;
