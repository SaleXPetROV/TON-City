import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, Map, ShoppingBag, Settings, User } from 'lucide-react';
import { useTranslation } from '@/lib/translations';

export default function MobileNav({ user }) {
  const location = useLocation();
  const navigate = useNavigate();
  const lang = localStorage.getItem('ton_city_lang') || 'en';
  const { t } = useTranslation(lang);

  // Не показываем на странице авторизации
  if (location.pathname.startsWith('/auth')) return null;
  // Не показываем если нет пользователя
  if (!user) return null;

  const navItems = [
    { icon: Home, label: t('home') || 'Home', path: '/' },
    { icon: Map, label: t('map') || 'Map', path: '/game' },
    { icon: ShoppingBag, label: t('market') || 'Market', path: '/trading' },
    { icon: Settings, label: t('settings') || 'Settings', path: '/settings' },
  ];

  return (
    <motion.nav
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      className="fixed bottom-0 left-0 right-0 z-50 lg:hidden bg-black/90 backdrop-blur-xl border-t border-white/10 safe-area-bottom"
    >
      <div className="flex items-center justify-around py-2 px-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all min-w-[60px]
                ${isActive 
                  ? 'text-cyber-cyan' 
                  : 'text-white/40 active:text-white'
                }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'drop-shadow-[0_0_8px_rgba(0,240,255,0.5)]' : ''}`} />
              <span className="text-[10px] font-medium uppercase tracking-wider">
                {item.label}
              </span>
              {isActive && (
                <motion.div
                  layoutId="mobile-nav-indicator"
                  className="absolute -top-0.5 w-8 h-0.5 bg-cyber-cyan rounded-full"
                />
              )}
            </button>
          );
        })}
      </div>
    </motion.nav>
  );
}
