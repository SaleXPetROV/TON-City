import { BrowserRouter, Routes, Route } from "react-router-dom";
import { TonConnectUIProvider } from "@tonconnect/ui-react";
import { Toaster } from "@/components/ui/sonner";
import LandingPage from "@/pages/LandingPage";
import GamePage from "@/pages/GamePage";
import DashboardPage from "@/pages/DashboardPage";
import AdminPage from "@/pages/AdminPage";
import IncomeTablePage from "@/pages/IncomeTablePage";
import "@/App.css";

const manifestUrl = `${window.location.origin}/tonconnect-manifest.json`;

function App() {
  return (
    <TonConnectUIProvider manifestUrl={manifestUrl}>
      <div className="App min-h-screen bg-void">
        {/* Noise overlay */}
        <div className="noise-overlay" />
        
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/game" element={<GamePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/income-table" element={<IncomeTablePage />} />
          </Routes>
        </BrowserRouter>
        
        <Toaster 
          position="bottom-right"
          toastOptions={{
            style: {
              background: '#0A0A0C',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#EDEDED',
              fontFamily: 'Rajdhani, sans-serif',
            },
          }}
        />
      </div>
    </TonConnectUIProvider>
  );
}

export default App;
