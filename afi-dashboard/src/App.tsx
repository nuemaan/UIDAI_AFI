import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import NationalOverview from "./pages/NationalOverview";
import StateComparison from "./pages/StateComparison";
import DistrictHotspots from "./pages/DistrictHotspots";
import AFIDecomposition from "./pages/AFIDecomposition";
import DistrictTypologies from "./pages/DistrictTypologies";
import DataUpload from "./pages/DataUpload";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<NationalOverview />} />
            <Route path="/states" element={<StateComparison />} />
            <Route path="/districts" element={<DistrictHotspots />} />
            <Route path="/decomposition" element={<AFIDecomposition />} />
            <Route path="/typologies" element={<DistrictTypologies />} />
            <Route path="/upload" element={<DataUpload />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
