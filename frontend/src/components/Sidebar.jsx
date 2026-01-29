import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { LayoutDashboard, Globe, ShoppingBag, Users, Lock, Settings, Map } from 'lucide-react';
import { useTranslation } from '@/lib/translations';

export default function Sidebar({ user }) {
  const location = useLocation();
  const navigate = useNavigate();
  const isHomePage = location.pathname === '/';
  const [isHovered, setIsHovered] = useState(false);
  const lang = localStorage.getItem('ton_city_lang') || 'en';
  const { t } = useTranslation(lang);

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
      className={`fixed left-4 top-24 z-50 hidden lg:flex flex-col
        transition-all duration-300 ${isExpanded ? 'w-56' : 'w-16'}`}
    >
      <div className="flex flex-col">
        {/* Надпись NAVIGATION - горизонтальная */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 0.4, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="text-[9px] text-cyber-cyan font-unbounded tracking-[0.5em]
                uppercase select-none mb-3 pl-4"
            >
              {t('navigation') || 'Navigation'}
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex flex-col gap-1.5 p-2 bg-black/70 backdrop-blur-xl border border-white/5 rounded-2xl shadow-2xl overflow-hidden">
          <NavItem icon={<LayoutDashboard className="w-5 h-5" />} label={t('city') || 'City'} path="/map" isExpanded={isExpanded} />
          <NavItem icon={<Map className="w-5 h-5" />} label={t('map') || 'Map'} path="/map" isExpanded={isExpanded} />
          <NavItem icon={<ShoppingBag className="w-5 h-5" />} label={t('market') || 'Market'} path="/trading" isExpanded={isExpanded} />
          <NavItem icon={<Users className="w-5 h-5" />} label={t('trading') || 'Trading'} path="/income-table" isExpanded={isExpanded} />
          {user.is_admin && (
            <NavItem icon={<Lock className="w-5 h-5" />} label={t('admin') || 'Admin'} path="/admin" isExpanded={isExpanded} />
          )}
          <div className="h-px bg-white/5 mx-2 my-1" />
          <NavItem icon={<Settings className="w-5 h-5" />} label={t('settings') || 'Settings'} path="/settings" isExpanded={isExpanded} />
        </div>
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
            ? 'text-cyber-cyan bg-cyber-cyan/10 border border-cyber-cyan/20' 
            : 'text-white/40 hover:bg-white/5 hover:text-white border border-transparent'
          }`}
      >
        <div className="min-w-[20px] flex items-center justify-center">{icon}</div>
        <AnimatePresence>
          {isExpanded && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="font-bold text-xs uppercase tracking-widest whitespace-nowrap overflow-hidden"
            >
              {label}
            </motion.span>
          )}
        </AnimatePresence>
      </div>
    );
  }
}
