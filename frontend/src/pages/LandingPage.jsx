import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { TonConnectButton, useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Building2, Coins, Users, TrendingUp, Zap, MapPin, 
  Calculator, Globe, GraduationCap, UserCircle, 
  Lock, LayoutDashboard, ShoppingBag, Settings 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { getGameStats } from '@/lib/api';
import { useTranslation } from '@/lib/translations';
import { toast } from 'sonner';
import TutorialModal from '@/components/TutorialModal';
import { useLocation } from 'react-router-dom';

export default function LandingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const isHome = location.pathname === '/';
  const [isNavHovered, setIsNavHovered] = useState(false);
  const isNavExpanded = isHome || isNavHovered;
  const wallet = useTonWallet();
  const [stats, setStats] = useState(null);
  const [user, setUser] = useState(null);
  const [showTutorial, setShowTutorial] = useState(false);
  const [lang, setLang] = useState(localStorage.getItem('ton_city_lang') || 'en');
  const { t } = useTranslation(lang);

  // Features array
  const features = [
    {
      icon: <Building2 className="w-8 h-8" />,
      title: lang === 'ru' ? 'Строй город' : 'Build City',
      description: lang === 'ru' ? 'Создавай бизнесы и развивай свою империю' : 'Create businesses and grow your empire'
    },
    {
      icon: <Coins className="w-8 h-8" />,
      title: lang === 'ru' ? 'Зарабатывай' : 'Earn Money',
      description: lang === 'ru' ? 'Получай доход от своих предприятий' : 'Get income from your businesses'
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: lang === 'ru' ? 'Торгуй' : 'Trade',
      description: lang === 'ru' ? 'Заключай контракты с другими игроками' : 'Make deals with other players'
    },
    {
      icon: <TrendingUp className="w-8 h-8" />,
      title: lang === 'ru' ? 'Расти' : 'Grow',
      description: lang === 'ru' ? 'Масштабируй бизнес на блокчейне TON' : 'Scale business on TON blockchain'
    }
  ];

  const changeLang = (newLang) => {
    setLang(newLang);
    localStorage.setItem('ton_city_lang', newLang);
  };

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await fetch('/api/auth/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          localStorage.removeItem('token');
          setUser(null);
        }
      } catch (error) {
        console.error("Auth check failed", error);
      }
    }
  }, []);

  const loadStats = async () => {
    try {
      const data = await getGameStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  useEffect(() => {
    loadStats();
    checkAuth();
  }, [checkAuth]);

  // Вспомогательный компонент для боковых иконок
  const NavIcon = ({ icon, label, onClick, isVisible = true }) => {
    if (!isVisible) return null;
    return (
      <div 
        onClick={onClick}
        className="group relative p-3 text-white/40 hover:text-cyber-cyan hover:bg-cyber-cyan/10 rounded-xl transition-all cursor-pointer border border-transparent hover:border-cyber-cyan/20"
      >
        {icon}
        {isNavExpanded && (
          <span className="absolute left-16 bg-cyber-cyan text-black text-[10px] font-bold px-2 py-1 rounded uppercase tracking-widest whitespace-nowrap z-50">
            {label}
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-void relative overflow-hidden font-rajdhani">
      {/* Сетка на фоне */}
      <div className="absolute inset-0 opacity-10 pointer-events-none">
        <div 
          className="absolute inset-0"
          style={{
            backgroundImage: `linear-gradient(rgba(0, 240, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 240, 255, 0.1) 1px, transparent 1px)`,
            backgroundSize: '50px 50px',
          }}
        />
      </div>

      {/* ЛЕВАЯ НАВИГАЦИЯ (Картинка 2) */}
      <AnimatePresence>
        {user && (
          <motion.div 
            initial={{ x: -100, opacity: 0 }} 
            animate={{ x: 0, opacity: 1 }}
            onMouseEnter={() => setIsNavHovered(true)}
            onMouseLeave={() => setIsNavHovered(false)}
            className={`fixed left-6 top-0 bottom-0 z-40 hidden lg:flex flex-col justify-center gap-8
              transition-all duration-300
              ${isNavExpanded ? 'w-56' : 'w-16'}
            `}
          >
        
            <div className="flex flex-col items-center gap-6">
              {/* Вертикальный заголовок */}
              <div 
                className="text-[10px] text-cyber-cyan/30 font-unbounded tracking-[0.8em] uppercase select-none mb-4"
                style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
              >
                Navigation
              </div>

              {/* Панель иконок */}
              <div className="flex flex-col gap-3 p-2 bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl shadow-2xl shadow-black/50">
                <NavIcon icon={<LayoutDashboard className="w-5 h-5" />} label="Dashboard" onClick={() => navigate('/game')} />
                <NavIcon icon={<Globe className="w-5 h-5" />} label="World Map" onClick={() => navigate('/map')} />
                <NavIcon icon={<ShoppingBag className="w-5 h-5" />} label="Market" onClick={() => navigate('/market')} />
                <NavIcon icon={<Users className="w-5 h-5" />} label="Citizens" onClick={() => navigate('/social')} />
                <NavIcon icon={<Lock className="w-5 h-5" />} label="Admin" onClick={() => navigate('/admin')} isVisible={user.is_admin} />
                <div className="h-px bg-white/5 mx-2 my-1" />
                <NavIcon icon={<Settings className="w-5 h-5" />} label="Settings" onClick={() => navigate('/settings')} />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative z-10">
        {/* HEADER */}
        <header className="container mx-auto px-6 py-6">
          <nav className="flex items-center justify-between">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3 cursor-pointer"
              onClick={() => navigate('/')}
            >
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyber-cyan to-neon-purple flex items-center justify-center shadow-lg shadow-cyber-cyan/20">
                <Building2 className="w-6 h-6 text-black" />
              </div>
              <span className="font-unbounded text-xl font-bold text-text-main tracking-tighter">
                TON <span className="text-cyber-cyan">CITY</span>
              </span>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-4"
            >
              <Select value={lang} onValueChange={changeLang}>
                <SelectTrigger className="w-28 bg-panel/30 border-white/5 text-text-main hover:border-cyber-cyan/50 transition-colors h-10">
                  <Globe className="w-4 h-4 mr-2 text-cyber-cyan" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-panel border-grid-border">
                  <SelectItem value="en">EN</SelectItem>
                  <SelectItem value="ru">RU</SelectItem>
                </SelectContent>
              </Select>

              {/* АВАТАР ИЛИ КНОПКИ (Картинка 1) */}
              <div className="flex items-center">
                {user ? (
                  <motion.div 
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    onClick={() => navigate('/game')}
                    className="flex items-center gap-3 bg-white/5 p-1.5 pr-4 rounded-full border border-white/10 cursor-pointer hover:bg-white/10 transition-all group"
                  >
                    <div className="w-9 h-9 bg-gradient-to-br from-cyber-cyan to-neon-purple rounded-full flex items-center justify-center font-bold text-black border-2 border-cyber-cyan shadow-[0_0_15px_rgba(0,255,243,0.3)] group-hover:shadow-cyber-cyan/50 transition-all">
                      {(user.display_name || user.username || 'U')[0].toUpperCase()}
                    </div>
                    <div className="text-left hidden sm:block">
                      <p className="text-[9px] text-cyber-cyan font-mono uppercase leading-none tracking-widest opacity-70">
                        {user.level || 'CITIZEN'}
                      </p>
                      <p className="text-sm font-bold text-white tracking-tight">
                        {user.display_name || user.username}
                      </p>
                    </div>
                  </motion.div>
                ) : (
                  <div className="flex items-center gap-2 bg-black/20 p-1 rounded-xl border border-white/5">
                    <Button 
                      variant="ghost" 
                      onClick={() => navigate('/auth?mode=login')}
                      className="text-text-main hover:bg-white/10 px-4 h-9"
                    >
                      {lang === 'ru' ? 'Вход' : 'Log In'}
                    </Button>
                    <Button 
                      onClick={() => navigate('/auth?mode=register')}
                      className="bg-cyber-cyan text-black hover:bg-cyber-cyan/80 px-5 h-9 font-unbounded text-[10px] font-bold rounded-lg shadow-lg shadow-cyber-cyan/20"
                    >
                      {lang === 'ru' ? 'ИГРАТЬ' : 'PLAY'}
                    </Button>
                  </div>
                )}
              </div>
            </motion.div>
          </nav>
        </header>

        {/* HERO CONTENT */}
        <main className="container mx-auto px-6 pt-12 pb-24">
          <div className="max-w-4xl mx-auto text-center">
            <motion.h1 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              className="font-unbounded text-4xl sm:text-5xl lg:text-7xl font-black text-text-main mb-6 leading-tight uppercase"
            >
              {t('title')}{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyber-cyan to-neon-purple animate-pulse">
                {t('subtitle')}
              </span>
            </motion.h1>

            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-lg text-text-muted mb-10 max-w-2xl mx-auto"
            >
              {t('description')}
            </motion.p>

            <div className="flex flex-wrap items-center justify-center gap-4 mb-16">
              <Button 
                onClick={() => user ? navigate('/game') : navigate('/auth?mode=register')}
                className="bg-cyber-cyan text-black px-8 py-7 font-unbounded text-sm font-bold rounded-2xl shadow-xl shadow-cyber-cyan/20 hover:scale-105 transition-transform"
              >
                {user ? (lang === 'ru' ? 'В ГОРОД' : 'TO CITY') : (lang === 'ru' ? 'НАЧАТЬ СТРОЙКУ' : 'START BUILDING')}
              </Button>
              
              <Button 
                variant="outline"
                onClick={() => setShowTutorial(true)}
                className="border-white/10 bg-white/5 text-white px-8 py-7 font-unbounded text-sm hover:bg-white/10"
              >
                <GraduationCap className="w-5 h-5 mr-2 text-neon-purple" />
                {t('tutorial') || (lang === 'ru' ? 'ОБУЧЕНИЕ' : 'TUTORIAL')}
              </Button>
            </div>

            {/* СТАТИСТИКА */}
            {stats && (
              <motion.div 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-20"
              >
                {[
                  { label: t('players'), value: stats.total_players, color: 'text-cyber-cyan' },
                  { label: t('plotsBought'), value: stats.owned_plots, color: 'text-cyber-cyan' },
                  { label: t('businesses'), value: stats.total_businesses, color: 'text-cyber-cyan' },
                  { label: t('tonInCirculation'), value: stats.total_volume_ton?.toFixed(1), color: 'text-signal-amber' }
                ].map((s, i) => (
                  <div key={i} className="glass-panel rounded-2xl p-6 border border-white/5 bg-white/2">
                    <div className={`text-3xl font-mono ${s.color} font-bold mb-1`}>{s.value || 0}</div>
                    <div className="text-[10px] text-text-muted uppercase tracking-[0.2em]">{s.label}</div>
                  </div>
                ))}
              </motion.div>
            )}
          </div>

          {/* КАРТОЧКИ ФУНКЦИЙ */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className="glass-panel group hover:border-cyber-cyan/30 rounded-3xl p-8 transition-all relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                   <feature.icon className="w-20 h-20 text-white" />
                </div>
                <div className="w-12 h-12 rounded-xl bg-cyber-cyan/10 flex items-center justify-center mb-6 border border-cyber-cyan/20">
                  <feature.icon className="w-6 h-6 text-cyber-cyan" />
                </div>
                <h3 className="font-unbounded text-lg font-bold text-white mb-3 uppercase tracking-tight">
                  {feature.title}
                </h3>
                <p className="text-text-muted text-sm leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </main>

        <footer className="border-t border-white/5 py-12 mt-12 bg-black/20">
          <div className="container mx-auto px-6 text-center">
            <div className="flex items-center justify-center gap-2 mb-4 opacity-50">
              <Building2 className="w-5 h-5" />
              <span className="font-unbounded text-xs font-bold uppercase tracking-widest">Ton City Builder</span>
            </div>
            <p className="text-text-muted text-[10px] uppercase tracking-widest">
              © 2025 Powered by TON Blockchain & Telegram Ecosystem
            </p>
          </div>
        </footer>
      </div>

      <TutorialModal 
        isOpen={showTutorial} 
        onClose={() => setShowTutorial(false)} 
        lang={lang}
      />
    </div>
  );
}
