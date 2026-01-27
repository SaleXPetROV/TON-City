import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LayoutDashboard, Globe, ShoppingBag, Users, Lock, Settings, Building2 } from 'lucide-react';

export default function Sidebar({ user }) {
    const location = useLocation();
    const navigate = useNavigate();
    const isHomePage = location.pathname === '/';


  // Если юзер не залогинен, не показываем меню вообще
  if (!user) return null;

  return (
    <div
  className="fixed left-6 top-0 bottom-0 z-50 flex flex-col justify-center group/sidebar
  w-20 hover:w-60 transition-all duration-300"
>

      <div className="flex flex-col gap-4">
        {/* Надпись NAVIGATION: видна только на главной или при ховере */}
        <div
            className={`text-[10px] text-cyber-cyan/30 font-unbounded tracking-[0.8em]
            uppercase select-none mb-2 self-center whitespace-nowrap
            ${isHomePage ? 'opacity-100' : 'group-hover/sidebar:opacity-0'}
            transition-opacity`}
            style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
            Navigation
        </div>


        <div className="flex flex-col gap-2 p-2 bg-black/60 backdrop-blur-xl border border-white/5 rounded-2xl shadow-2xl overflow-hidden">
          <NavItem icon={<LayoutDashboard />} label="City" path="/game" isHomePage={isHomePage} />
          <NavItem icon={<Globe />} label="Map" path="/dashboard" isHomePage={isHomePage} />
          <NavItem icon={<ShoppingBag />} label="Market" path="/trading" isHomePage={isHomePage} />
          <NavItem icon={<Lock />} label="Admin" path="/admin" isVisible={user.is_admin} isHomePage={isHomePage} />
          <div className="h-px bg-white/5 mx-2 my-1" />
          <NavItem icon={<Settings />} label="Settings" path="/settings" isHomePage={isHomePage} />
        </div>
      </div>
    </div>
  );

  function NavItem({ icon, label, path, isVisible = true, isHomePage }) {
    if (!isVisible) return null;
    const isActive = location.pathname === path;
    
    return (
      <div 
        onClick={() => navigate(path)}
        className={`relative flex items-center gap-4 p-3 rounded-xl cursor-pointer transition-all
          ${isActive ? 'text-cyber-cyan bg-cyber-cyan/10' : 'text-white/40 hover:bg-white/5 hover:text-white'}`}
      >
        <div className="min-w-[24px]">{icon}</div>
        <span
  className={`font-bold text-xs uppercase tracking-widest whitespace-nowrap ml-4
    ${isHomePage ? 'opacity-100' : 'opacity-0'}
    group-hover/sidebar:opacity-100 transition-opacity`}
>
  {label}
</span>

      </div>
    );
  }
}