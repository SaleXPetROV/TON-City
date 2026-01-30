import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShoppingBag, Lock, Settings, Map, Store,
  Trophy, Calculator, GraduationCap, Building2, MessageCircle
} from 'lucide-react';

export default function Sidebar({ user }) {
  const location = useLocation();
  const navigate = useNavigate();
  const isHomePage = location.pathname === '/';
  const [isHovered, setIsHovered] = useState(false);

  // Sidebar открыт всегда на главной ИЛИ при наведении на других страницах
  const isExpanded = isHomePage || isHovered;

  // Если юзер не залогинен, не показываем меню вообще
  if (!user) return null;

  return (
    <motion.div
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`fixed left-4 top-24 z-40 hidden lg:flex flex-col
        transition-all duration-300 ${isExpanded ? 'w-52' : 'w-14'}`}
    >
      <div className="flex flex-col gap-1.5 p-2 bg-gradient-to-b from-[#1a1a2e] to-[#0f0f1a] backdrop-blur-xl border border-cyber-cyan/20 rounded-2xl shadow-2xl shadow-cyber-cyan/10">
        <NavItem icon={<Map className="w-5 h-5" />} label="Карта" path="/map" isExpanded={isExpanded} />
        <NavItem icon={<Building2 className="w-5 h-5" />} label="Мои бизнесы" path="/my-businesses" isExpanded={isExpanded} />
        <NavItem icon={<Store className="w-5 h-5" />} label="Маркетплейс" path="/marketplace" isExpanded={isExpanded} />
        <NavItem icon={<ShoppingBag className="w-5 h-5" />} label="Торговля" path="/trading" isExpanded={isExpanded} />
        <NavItem icon={<Trophy className="w-5 h-5" />} label="Рейтинг" path="/leaderboard" isExpanded={isExpanded} />
        <NavItem icon={<Calculator className="w-5 h-5" />} label="Калькулятор" path="/calculator" isExpanded={isExpanded} />
        <NavItem icon={<GraduationCap className="w-5 h-5" />} label="Обучение" path="/tutorial" isExpanded={isExpanded} />
        {user.is_admin && (
          <NavItem icon={<Lock className="w-5 h-5" />} label="Админ" path="/admin" isExpanded={isExpanded} />
        )}
        <div className="h-px bg-cyber-cyan/20 mx-2 my-1" />
        <NavItem icon={<Settings className="w-5 h-5" />} label="Настройки" path="/settings" isExpanded={isExpanded} />
        <a 
          href="https://t.me/your_support_bot" 
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
  );

  function NavItem({ icon, label, path, isExpanded }) {
    const isActive = location.pathname === path;
    
    return (
      <div 
        onClick={() => navigate(path)}
        className={`relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all
          ${isActive 
            ? 'text-cyber-cyan bg-cyber-cyan/20 border border-cyber-cyan/30 shadow-lg shadow-cyber-cyan/10' 
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
