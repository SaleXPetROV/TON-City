import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, Map, ShoppingBag, Settings, MessageCircle, Menu, X,
  Building2, Trophy, Calculator, GraduationCap, Store, Wallet,
  ArrowDownToLine, ArrowUpFromLine, Shield
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTranslation } from '@/lib/translations';

export default function MobileNav({ user }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const lang = localStorage.getItem('ton_city_lang') || 'en';
  const { t } = useTranslation(lang);

  // Не показываем на странице авторизации
  if (location.pathname.startsWith('/auth')) return null;
  // Не показываем если нет пользователя
  if (!user) return null;

  const menuItems = [
    { icon: Home, label: t('home') || 'Главная', path: '/' },
    { icon: Map, label: t('map') || 'Карта', path: '/map' },
    { icon: Building2, label: 'Мои бизнесы', path: '/my-businesses' },
    { icon: Store, label: 'Маркетплейс', path: '/marketplace' },
    { icon: ShoppingBag, label: 'Торговля', path: '/trading' },
    { icon: Trophy, label: 'Рейтинг', path: '/leaderboard' },
    { icon: MessageCircle, label: 'Чат', path: '/chat' },
    { icon: Calculator, label: 'Калькулятор', path: '/calculator' },
    { icon: GraduationCap, label: 'Обучение', path: '/tutorial' },
    { icon: Settings, label: 'Настройки', path: '/settings' },
  ];

  // Если пользователь - админ, добавляем ссылку на админку
  if (user?.is_admin) {
    menuItems.push({ icon: Shield, label: 'Админка', path: '/admin' });
  }

  const handleNavigation = (path) => {
    navigate(path);
    setIsMenuOpen(false);
  };

  return (
    <>
      {/* Hamburger Button - Fixed Top Left (only on mobile) */}
      <div className="lg:hidden fixed top-4 left-3 z-[60]">
        <Button
          data-testid="mobile-menu-toggle"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          variant="ghost"
          size="icon"
          className={`w-10 h-10 rounded-xl transition-all duration-300 ${
            isMenuOpen 
              ? 'bg-cyber-cyan text-black' 
              : 'bg-black/80 backdrop-blur-xl border border-white/10 text-white hover:bg-white/10'
          }`}
        >
          {isMenuOpen ? (
            <X className="w-5 h-5" />
          ) : (
            <Menu className="w-5 h-5" />
          )}
        </Button>
      </div>

      {/* Fullscreen Menu Overlay */}
      <AnimatePresence>
        {isMenuOpen && (
          <motion.div
            data-testid="mobile-menu-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="lg:hidden fixed inset-0 z-50 bg-void/98 backdrop-blur-xl"
          >
            {/* Background Grid Effect */}
            <div className="absolute inset-0 opacity-5 pointer-events-none">
              <div 
                className="absolute inset-0"
                style={{
                  backgroundImage: `linear-gradient(rgba(0, 240, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 240, 255, 0.1) 1px, transparent 1px)`,
                  backgroundSize: '40px 40px',
                }}
              />
            </div>

            {/* Menu Content */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 20, opacity: 0 }}
              transition={{ delay: 0.1, duration: 0.3 }}
              className="relative h-full flex flex-col pt-24 px-6 pb-8 overflow-y-auto"
            >
              {/* User Profile Card */}
              <div className="mb-8 p-4 bg-gradient-to-r from-cyber-cyan/10 to-neon-purple/10 rounded-2xl border border-cyber-cyan/20">
                <div className="flex items-center gap-4">
                  {user.avatar ? (
                    <img 
                      src={user.avatar} 
                      alt={user.username}
                      className="w-14 h-14 rounded-full border-2 border-cyber-cyan shadow-lg shadow-cyber-cyan/30"
                    />
                  ) : (
                    <div className="w-14 h-14 bg-gradient-to-br from-cyber-cyan to-neon-purple rounded-full flex items-center justify-center text-xl font-bold text-black">
                      {(user.display_name || user.username || 'U')[0].toUpperCase()}
                    </div>
                  )}
                  <div className="flex-1">
                    <p className="text-xs text-cyber-cyan font-mono uppercase tracking-widest">CITIZEN</p>
                    <p className="text-lg font-bold text-white">{user.display_name || user.username}</p>
                    <p className="text-sm text-text-muted">Level {user.level || 1}</p>
                  </div>
                </div>
                
                {/* Balance */}
                <div className="mt-4 p-3 bg-black/30 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Wallet className="w-4 h-4 text-cyber-cyan" />
                      <span className="text-xs text-text-muted uppercase">Баланс</span>
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {(user.balance_ton || 0).toFixed(2)} <span className="text-cyber-cyan text-sm">TON</span>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <Button
                    size="sm"
                    className="bg-green-600 hover:bg-green-700 text-xs h-10"
                    onClick={() => handleNavigation('/settings')}
                  >
                    <ArrowDownToLine className="w-4 h-4 mr-2" />
                    Пополнить
                  </Button>
                  <Button
                    size="sm"
                    className="bg-orange-600 hover:bg-orange-700 text-xs h-10"
                    onClick={() => handleNavigation('/settings')}
                  >
                    <ArrowUpFromLine className="w-4 h-4 mr-2" />
                    Вывести
                  </Button>
                </div>
              </div>

              {/* Menu Items */}
              <nav className="flex-1 space-y-2">
                {menuItems.map((item, index) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  
                  return (
                    <motion.button
                      key={item.path}
                      data-testid={`mobile-menu-item-${item.path.replace('/', '') || 'home'}`}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: 0.05 * index }}
                      onClick={() => handleNavigation(item.path)}
                      className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all ${
                        isActive 
                          ? 'bg-cyber-cyan/20 border border-cyber-cyan/30 text-cyber-cyan' 
                          : 'bg-white/5 border border-transparent text-white hover:bg-white/10 hover:border-white/10'
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        isActive ? 'bg-cyber-cyan/20' : 'bg-white/5'
                      }`}>
                        <Icon className={`w-5 h-5 ${isActive ? 'text-cyber-cyan' : 'text-white/70'}`} />
                      </div>
                      <span className="text-base font-semibold uppercase tracking-wide">
                        {item.label}
                      </span>
                      {isActive && (
                        <div className="ml-auto w-2 h-2 rounded-full bg-cyber-cyan shadow-lg shadow-cyber-cyan/50" />
                      )}
                    </motion.button>
                  );
                })}
              </nav>

              {/* Footer */}
              <div className="mt-6 pt-4 border-t border-white/10 text-center">
                <p className="text-[10px] text-text-muted uppercase tracking-widest">
                  TON City Builder © 2025
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
