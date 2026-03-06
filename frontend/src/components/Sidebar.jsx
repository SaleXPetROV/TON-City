import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Settings, Map, Store, Trophy, Calculator, 
  GraduationCap, Building2, MessageCircle, ShoppingBag,
  ArrowDownToLine, ArrowUpFromLine, Wallet, Landmark, History,
  Shield, User
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DepositModal, WithdrawModal } from './BalanceModals';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

export default function Sidebar({ user, onBalanceUpdate }) {
  const location = useLocation();
  const navigate = useNavigate();
  const isHomePage = location.pathname === '/';
  const [isHovered, setIsHovered] = useState(false);
  const [supportLink, setSupportLink] = useState('https://t.me/support');
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [balance, setBalance] = useState(user?.balance_ton || 0);
  const [depositAddress, setDepositAddress] = useState('');

  useEffect(() => {
    // Fetch support link and deposit address from config
    fetch(`${API}/config`)
      .then(r => r.json())
      .then(data => {
        if (data.support_telegram) {
          setSupportLink(data.support_telegram);
        }
        if (data.deposit_address) {
          setDepositAddress(data.deposit_address);
        }
      })
      .catch(() => {});
  }, []);

  // Update balance when user changes
  useEffect(() => {
    if (user?.balance_ton !== undefined) {
      setBalance(user.balance_ton);
    }
  }, [user?.balance_ton]);

  // Refresh balance periodically
  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const token = localStorage.getItem('token') || localStorage.getItem('ton_city_token');
        if (!token) return;
        const response = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setBalance(response.data.balance_ton || 0);
      } catch (error) {
        // Silent fail
      }
    };

    const interval = setInterval(fetchBalance, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleDepositSuccess = () => {
    // Refresh balance after deposit
    setTimeout(async () => {
      try {
        const token = localStorage.getItem('token') || localStorage.getItem('ton_city_token');
        if (!token) return;
        const response = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setBalance(response.data.balance_ton || 0);
        if (onBalanceUpdate) onBalanceUpdate(response.data.balance_ton);
      } catch (error) {}
    }, 3000);
  };

  const handleWithdrawSuccess = () => {
    // Refresh balance after withdrawal
    setTimeout(async () => {
      try {
        const token = localStorage.getItem('token') || localStorage.getItem('ton_city_token');
        if (!token) return;
        const response = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setBalance(response.data.balance_ton || 0);
        if (onBalanceUpdate) onBalanceUpdate(response.data.balance_ton);
      } catch (error) {}
    }, 1000);
  };

  // Sidebar открыт всегда на главной ИЛИ при наведении на других страницах
  const isExpanded = isHomePage || isHovered;

  // Если юзер не залогинен, не показываем меню вообще
  if (!user) return null;

  return (
    <>
      <motion.div
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`fixed left-4 top-4 z-40 hidden lg:flex flex-col
          transition-all duration-300 ${isExpanded ? 'w-52' : 'w-14'}`}
      >
        <div className="flex flex-col gap-1.5 p-2 bg-gradient-to-b from-[#1a1a2e] to-[#0f0f1a] backdrop-blur-xl border border-cyber-cyan/20 rounded-2xl shadow-2xl shadow-cyber-cyan/10">
          
          {/* Logo - always visible, links to home */}
          <div 
            className="flex items-center gap-2 p-2 cursor-pointer hover:bg-white/5 rounded-xl transition-colors mb-1"
            onClick={() => navigate('/')}
            data-testid="sidebar-logo"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyber-cyan to-neon-purple flex items-center justify-center shadow-lg shadow-cyber-cyan/20 flex-shrink-0">
              <Building2 className="w-5 h-5 text-black" />
            </div>
            {isExpanded && (
              <span className="font-unbounded text-sm font-bold text-text-main tracking-tighter whitespace-nowrap">
                TON <span className="text-cyber-cyan">CITY</span>
              </span>
            )}
          </div>
          
          {/* Balance Section */}
          <div className={`p-3 bg-gradient-to-r from-cyber-cyan/10 to-purple-500/10 rounded-xl border border-cyber-cyan/20 mb-2 ${!isExpanded ? 'hidden' : ''}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Wallet className="w-4 h-4 text-cyber-cyan" />
                <span className="text-xs text-text-muted uppercase tracking-wider">Баланс</span>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => navigate('/history')}
                  className="w-6 h-6 text-text-muted hover:text-white hover:bg-white/10"
                  title="История операций"
                >
                  <History className="w-4 h-4" />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => navigate('/settings')}
                  className="w-6 h-6 text-text-muted hover:text-white hover:bg-white/10"
                  title="Настройки"
                >
                  <Settings className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <div className="text-xl font-bold text-white mb-3">
              {balance.toFixed(2)} <span className="text-cyber-cyan text-sm">TON</span>
            </div>
            <div className="flex flex-col gap-2">
              <Button
                size="sm"
                onClick={() => setShowDepositModal(true)}
                className="w-full bg-green-600 hover:bg-green-700 text-xs h-9"
              >
                <ArrowDownToLine className="w-4 h-4 mr-2" />
                Пополнить
              </Button>
              <Button
                size="sm"
                onClick={() => setShowWithdrawModal(true)}
                className="w-full bg-orange-600 hover:bg-orange-700 text-xs h-9"
              >
                <ArrowUpFromLine className="w-4 h-4 mr-2" />
                Вывести
              </Button>
            </div>
          </div>
          
          {/* Compact balance for collapsed state */}
          {!isExpanded && (
            <div 
              className="p-2 bg-cyber-cyan/10 rounded-xl text-center cursor-pointer hover:bg-cyber-cyan/20 transition-colors mb-2"
              onClick={() => setShowDepositModal(true)}
            >
              <Wallet className="w-5 h-5 text-cyber-cyan mx-auto" />
              <div className="text-xs text-cyber-cyan mt-1 font-bold">{balance.toFixed(1)}</div>
            </div>
          )}
          
          <NavItem icon={<Map className="w-5 h-5" />} label="Карта" path="/map" isExpanded={isExpanded} />
          <NavItem icon={<Building2 className="w-5 h-5" />} label="Мои бизнесы" path="/my-businesses" isExpanded={isExpanded} />
          <NavItem icon={<Store className="w-5 h-5" />} label="Маркетплейс" path="/marketplace" isExpanded={isExpanded} />
          <NavItem icon={<ShoppingBag className="w-5 h-5" />} label="Торговля" path="/trading" isExpanded={isExpanded} />
          <NavItem icon={<Landmark className="w-5 h-5" />} label="Кредиты" path="/credit" isExpanded={isExpanded} />
          <NavItem icon={<Trophy className="w-5 h-5" />} label="Рейтинг" path="/leaderboard" isExpanded={isExpanded} />
          <NavItem icon={<MessageCircle className="w-5 h-5" />} label="Чат" path="/chat" isExpanded={isExpanded} />
          <NavItem icon={<Calculator className="w-5 h-5" />} label="Калькулятор" path="/calculator" isExpanded={isExpanded} />
          <NavItem icon={<GraduationCap className="w-5 h-5" />} label="Обучение" path="/tutorial" isExpanded={isExpanded} />
          
          {/* Admin Panel Button - only for admins */}
          {user?.is_admin && (
            <>
              <div className="h-px bg-red-500/20 mx-2 my-1" />
              <NavItem 
                icon={<Shield className="w-5 h-5" />} 
                label="Админ-панель" 
                path="/admin" 
                isExpanded={isExpanded}
                isAdmin={true}
              />
            </>
          )}
          
          <div className="h-px bg-cyber-cyan/20 mx-2 my-1" />
          <a 
            href={supportLink}
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all text-green-400 hover:bg-green-500/10 border border-transparent"
          >
            <div className="min-w-[20px] flex items-center justify-center">
              <MessageCircle className="w-5 h-5" />
            </div>
            {isExpanded && (
              <span className="font-bold text-xs uppercase tracking-widest whitespace-nowrap">
                Поддержка
              </span>
            )}
          </a>
        </div>
      </motion.div>

      {/* Modals */}
      <DepositModal
        isOpen={showDepositModal}
        onClose={() => setShowDepositModal(false)}
        onSuccess={handleDepositSuccess}
        receiverAddress={depositAddress}
      />
      
      <WithdrawModal
        isOpen={showWithdrawModal}
        onClose={() => setShowWithdrawModal(false)}
        onSuccess={handleWithdrawSuccess}
        currentBalance={balance}
        userWallet={user?.wallet_address}
      />
    </>
  );

  function NavItem({ icon, label, path, isExpanded, isAdmin = false }) {
    const isActive = location.pathname === path;
    
    return (
      <div 
        onClick={() => navigate(path)}
        className={`relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all
          ${isActive 
            ? isAdmin
              ? 'text-red-400 bg-red-500/20 border border-red-500/30 shadow-lg shadow-red-500/10'
              : 'text-cyber-cyan bg-cyber-cyan/20 border border-cyber-cyan/30 shadow-lg shadow-cyber-cyan/10' 
            : isAdmin
              ? 'text-red-400/70 hover:bg-red-500/10 hover:text-red-400 border border-transparent'
              : 'text-white/70 hover:bg-white/10 hover:text-white border border-transparent'
          }`}
      >
        <div className="min-w-[20px] flex items-center justify-center">{icon}</div>
        {isExpanded && (
          <span className="font-bold text-xs uppercase tracking-widest whitespace-nowrap">
            {label}
          </span>
        )}
      </div>
    );
  }
}
