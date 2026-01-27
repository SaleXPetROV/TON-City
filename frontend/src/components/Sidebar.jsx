import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { LayoutDashboard, Globe, ShoppingBag, Users, Lock, Settings, Building2 } from 'lucide-react';

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
      className={`fixed left-6 top-0 bottom-0 z-50 hidden lg:flex flex-col justify-center
        transition-all duration-300 ${isExpanded ? 'w-60' : 'w-20'}`}
    >
      <div className="flex flex-col gap-4">
        {/* Надпись NAVIGATION - видна только когда sidebar расширен */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.3 }}
              exit={{ opacity: 0 }}
              className="text-[10px] text-cyber-cyan font-unbounded tracking-[0.8em]
                uppercase select-none mb-2 self-center whitespace-nowrap"
              style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
            >
              Navigation
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex flex-col gap-2 p-2 bg-black/60 backdrop-blur-xl border border-white/5 rounded-2xl shadow-2xl overflow-hidden">
          <NavItem icon={<LayoutDashboard className="w-5 h-5" />} label="City" path="/game" isExpanded={isExpanded} />
          <NavItem icon={<Globe className="w-5 h-5" />} label="Map" path="/dashboard" isExpanded={isExpanded} />
          <NavItem icon={<ShoppingBag className="w-5 h-5" />} label="Market" path="/trading" isExpanded={isExpanded} />
          <NavItem icon={<Users className="w-5 h-5" />} label="Trading" path="/income-table" isExpanded={isExpanded} />
          {user.is_admin && (
            <NavItem icon={<Lock className="w-5 h-5" />} label="Admin" path="/admin" isExpanded={isExpanded} />
          )}
          <div className="h-px bg-white/5 mx-2 my-1" />
          <NavItem icon={<Settings className="w-5 h-5" />} label="Settings" path="/settings" isExpanded={isExpanded} />
        </div>
      </div>
    </motion.div>
  );

  function NavItem({ icon, label, path, isExpanded }) {
    const isActive = location.pathname === path;
    
    return (
      <div 
        onClick={() => navigate(path)}
        className={`relative flex items-center gap-4 p-3 rounded-xl cursor-pointer transition-all
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