import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { TonConnectUIProvider } from "@tonconnect/ui-react";
import { Toaster } from "@/components/ui/sonner";
import LandingPage from "@/pages/LandingPage";
import GamePage from "@/pages/GamePage";
import DashboardPage from "@/pages/DashboardPage";
import AdminPage from "@/pages/AdminPage";
import IncomeTablePage from "@/pages/IncomeTablePage";
import TradingPage from "@/pages/TradingPage";
import AuthPage from '@/pages/AuthPage';
import Sidebar from '@/components/Sidebar';
import "@/App.css";

const manifestUrl = `${window.location.origin}/tonconnect-manifest.json`;

function App() {
  const [user, setUser] = useState(null);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const res = await fetch('/api/api/auth/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setUser(data);
        } else {
          localStorage.removeItem('token');
          setUser(null);
        }
      } catch (e) {
        console.error("Auth error:", e);
      }
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <TonConnectUIProvider manifestUrl={manifestUrl}>
      <div className="App min-h-screen bg-void">
        <div className="noise-overlay" />
        
        <BrowserRouter>
        {user && <Sidebar user={user} />}
          
          <Routes>
            <Route path="/" element={<LandingPage user={user} setUser={setUser} />} />
            <Route path="/auth" element={<AuthPage setUser={setUser} />} />
            <Route path="/game" element={<GamePage user={user} />} />
            <Route path="/dashboard" element={<DashboardPage user={user} />} />
            <Route path="/admin" element={<AdminPage user={user} />} />
            <Route path="/income-table" element={<IncomeTablePage user={user} />} />
            <Route path="/trading" element={<TradingPage user={user} />} />
          </Routes>
        </BrowserRouter>
        
        {/* Toaster должен быть здесь для работы уведомлений */}
        <Toaster position="bottom-right" theme="dark" closeButton richColors />
      </div>
    </TonConnectUIProvider>
  );
}

export default App;