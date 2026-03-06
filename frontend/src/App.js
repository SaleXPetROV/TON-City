import { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { TonConnectUIProvider } from "@tonconnect/ui-react";
import { Toaster } from "@/components/ui/sonner";
import LandingPage from "@/pages/LandingPage";
import GamePage from "@/pages/GamePage";
import MapPage from "@/pages/MapPage";
import TonIslandPage from "@/pages/TonIslandPage";
import DashboardPage from "@/pages/DashboardPage";
import AdminPage from "@/pages/AdminPage";
import IncomeTablePage from "@/pages/IncomeTablePage";
import TradingPage from "@/pages/TradingPageNew";
import MarketplacePage from "@/pages/MarketplacePage";
import MyBusinessesPage from "@/pages/MyBusinessesPage";
import LeaderboardPage from "@/pages/LeaderboardPage";
import TutorialPage from "@/pages/TutorialPage";
import ChatPage from "@/pages/ChatPage";
import AuthPage from '@/pages/AuthPage';
import SettingsPage from '@/pages/SettingsPage';
import ForgotPasswordPage from '@/pages/ForgotPasswordPage';
import SecurityPage from '@/pages/SecurityPage';
import TransactionHistoryPage from '@/pages/TransactionHistoryPage';
import CreditPage from '@/pages/CreditPage';
import MobileNav from '@/components/MobileNav';
import MaintenanceOverlay from '@/components/MaintenanceOverlay';
import "@/App.css";

const manifestUrl = `${window.location.origin}/tonconnect-manifest.json`;
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

function App() {
  const [user, setUser] = useState(null);
  
  // Function to refresh user balance
  const refreshBalance = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setUser(prev => prev ? { ...prev, balance_ton: data.balance_ton, plots_owned: data.plots_owned } : data);
      }
    } catch (e) {
      console.error("[App.js] refreshBalance error:", e);
    }
  }, []);
  
  // Function to update balance directly (for immediate updates)
  const updateBalance = useCallback((newBalance) => {
    setUser(prev => prev ? { ...prev, balance_ton: newBalance } : prev);
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    console.log('[App.js] checkAuth: token =', token ? 'exists' : 'null');
    
    if (token) {
      try {
        const res = await fetch(`${BACKEND_URL}/api/auth/me`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        console.log('[App.js] checkAuth: response status =', res.status);
        
        if (res.ok) {
          const data = await res.json();
          console.log('[App.js] checkAuth: user data =', data);
          setUser(data);
        } else {
          console.log('[App.js] checkAuth: invalid token, removing');
          localStorage.removeItem('token');
          setUser(null);
        }
      } catch (e) {
        console.error("[App.js] checkAuth error:", e);
        localStorage.removeItem('token');
        setUser(null);
      }
    } else {
      setUser(null);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  useEffect(() => {
    checkAuth();
    
    // Слушатель на изменение localStorage
    const handleStorageChange = (e) => {
      if (e.key === 'token') {
        checkAuth();
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  return (
    <TonConnectUIProvider manifestUrl={manifestUrl}>
      <div className="App min-h-screen bg-void">
        <div className="noise-overlay" />
        
        {/* Maintenance Overlay - shows for all users except admins (checked inside component) */}
        <MaintenanceOverlay />
        
        <BrowserRouter>
          {/* Mobile Bottom Navigation */}
          <MobileNav user={user} />
          
          <Routes>
            <Route path="/" element={<LandingPage user={user} setUser={setUser} />} />
            <Route path="/auth" element={<AuthPage setUser={setUser} onAuthSuccess={checkAuth} />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/map" element={<TonIslandPage user={user} refreshBalance={refreshBalance} updateBalance={updateBalance} />} />
            <Route path="/island" element={<TonIslandPage user={user} refreshBalance={refreshBalance} updateBalance={updateBalance} />} />
            <Route path="/game" element={<TonIslandPage user={user} refreshBalance={refreshBalance} updateBalance={updateBalance} />} />
            <Route path="/game/:cityId" element={<GamePage user={user} refreshBalance={refreshBalance} updateBalance={updateBalance} />} />
            <Route path="/dashboard" element={<DashboardPage user={user} refreshBalance={refreshBalance} />} />
            <Route path="/admin" element={<AdminPage user={user} />} />
            <Route path="/income-table" element={<IncomeTablePage user={user} />} />
            <Route path="/calculator" element={<IncomeTablePage user={user} />} />
            <Route path="/trading" element={<TradingPage user={user} refreshBalance={refreshBalance} updateBalance={updateBalance} />} />
            <Route path="/credit" element={<CreditPage user={user} refreshBalance={refreshBalance} updateBalance={updateBalance} />} />
            <Route path="/marketplace" element={<MarketplacePage user={user} refreshBalance={refreshBalance} updateBalance={updateBalance} />} />
            <Route path="/my-businesses" element={<MyBusinessesPage user={user} refreshBalance={refreshBalance} updateBalance={updateBalance} />} />
            <Route path="/leaderboard" element={<LeaderboardPage user={user} />} />
            <Route path="/tutorial" element={<TutorialPage user={user} />} />
            <Route path="/chat" element={<ChatPage user={user} />} />
            <Route path="/settings" element={<SettingsPage user={user} setUser={setUser} onLogout={handleLogout} refreshBalance={refreshBalance} />} />
            <Route path="/security" element={<SecurityPage user={user} />} />
            <Route path="/history" element={<TransactionHistoryPage user={user} />} />
          </Routes>
        </BrowserRouter>
        
        <Toaster position="bottom-right" theme="dark" closeButton richColors />
      </div>
    </TonConnectUIProvider>
  );
}

export default App;
