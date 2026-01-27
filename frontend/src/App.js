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
import SettingsPage from '@/pages/SettingsPage';
import Sidebar from '@/components/Sidebar';
import "@/App.css";

const manifestUrl = `${window.location.origin}/tonconnect-manifest.json`;

function App() {
  const [user, setUser] = useState(null);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    console.log('[App.js] checkAuth: token =', token ? 'exists' : 'null');
    
    if (token) {
      try {
        const res = await fetch('/api/auth/me', {
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

  useEffect(() => {
    checkAuth();
    
    // Добавим слушатель на изменение localStorage (для случая когда token обновляется в другой вкладке)
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
        
        <BrowserRouter>
          {user && <Sidebar user={user} />}
          
          <Routes>
            <Route path="/" element={<LandingPage user={user} setUser={setUser} />} />
            <Route path="/auth" element={<AuthPage setUser={setUser} onAuthSuccess={checkAuth} />} />
            <Route path="/game" element={<GamePage user={user} />} />
            <Route path="/dashboard" element={<DashboardPage user={user} />} />
            <Route path="/admin" element={<AdminPage user={user} />} />
            <Route path="/income-table" element={<IncomeTablePage user={user} />} />
            <Route path="/trading" element={<TradingPage user={user} />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </BrowserRouter>
        
        <Toaster position="bottom-right" theme="dark" closeButton richColors />
      </div>
    </TonConnectUIProvider>
  );
}

export default App;
