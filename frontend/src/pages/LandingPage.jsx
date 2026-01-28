import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TonConnectButton, useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import { motion } from 'framer-motion';
import { 
  Building2, Coins, Users, TrendingUp, Zap, MapPin, 
  Calculator, Globe, GraduationCap, UserCircle, 
  Lock, LayoutDashboard, ShoppingBag, Settings,
  Wallet, BarChart3, Shield, Trophy, Sparkles
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { getGameStats } from '@/lib/api';
import { useTranslation, languages } from '@/lib/translations';
import { toast } from 'sonner';
import TutorialModal from '@/components/TutorialModal';

export default function LandingPage({ user, setUser }) {
  const navigate = useNavigate();
  const wallet = useTonWallet();
  const [stats, setStats] = useState(null);
  const [showTutorial, setShowTutorial] = useState(false);
  const [lang, setLang] = useState(localStorage.getItem('ton_city_lang') || 'en');
  const { t } = useTranslation(lang);

  // Features array
  const features = [
    {
      icon: Building2,
      title: t('buildCity'),
      description: t('buildCityDesc')
    },
    {
      icon: Coins,
      title: t('earnMoney'),
      description: t('earnMoneyDesc')
    },
    {
      icon: Users,
      title: t('trade'),
      description: t('tradeDesc')
    },
    {
      icon: TrendingUp,
      title: t('grow'),
      description: t('growDesc')
    }
  ];

  // Game mechanics for info section
  const gameMechanics = [
    {
      icon: MapPin,
      title: t('buyLand') || 'Buy Land',
      desc: t('buyLandDesc') || 'Purchase plots in different city zones - from the expensive center to affordable outskirts'
    },
    {
      icon: Building2,
      title: t('buildBusiness') || 'Build Business',
      desc: t('buildBusinessDesc') || 'Construct farms, factories, shops, restaurants, banks and more'
    },
    {
      icon: Zap,
      title: t('produceResources') || 'Produce Resources',
      desc: t('produceResourcesDesc') || 'Your businesses produce resources that can be sold or used by other businesses'
    },
    {
      icon: BarChart3,
      title: t('earnIncome') || 'Earn Income',
      desc: t('earnIncomeDesc') || 'Get real TON cryptocurrency from your businesses every day'
    },
    {
      icon: Shield,
      title: t('secureBlockchain') || 'Secure Blockchain',
      desc: t('secureBlockchainDesc') || 'All transactions are recorded on TON blockchain - your assets are truly yours'
    },
    {
      icon: Trophy,
      title: t('levelUp') || 'Level Up',
      desc: t('levelUpDesc') || 'Grow your business empire, unlock new opportunities and climb the rankings'
    }
  ];

  const changeLang = (newLang) => {
    setLang(newLang);
    localStorage.setItem('ton_city_lang', newLang);
  };

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
  }, []);

  return (
    <div className="min-h-screen bg-void relative overflow-hidden font-rajdhani pb-20 lg:pb-0">
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

      <div className="relative z-10">
        {/* HEADER */}
        <header className="container mx-auto px-4 sm:px-6 py-4 sm:py-6">
          <nav className="flex items-center justify-between">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 sm:gap-3 cursor-pointer"
              onClick={() => navigate('/')}
            >
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br from-cyber-cyan to-neon-purple flex items-center justify-center shadow-lg shadow-cyber-cyan/20">
                <Building2 className="w-5 h-5 sm:w-6 sm:h-6 text-black" />
              </div>
              <span className="font-unbounded text-lg sm:text-xl font-bold text-text-main tracking-tighter">
                TON <span className="text-cyber-cyan">CITY</span>
              </span>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 sm:gap-4"
            >
              <Select value={lang} onValueChange={changeLang}>
                <SelectTrigger className="w-20 sm:w-32 bg-panel/30 border-white/5 text-text-main hover:border-cyber-cyan/50 transition-colors h-8 sm:h-10 text-xs sm:text-sm">
                  <Globe className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2 text-cyber-cyan" />
                  <SelectValue>
                    {languages.find(l => l.code === lang)?.flag}
                    <span className="hidden sm:inline ml-1">{lang.toUpperCase()}</span>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent className="bg-panel border-grid-border">
                  {languages.map(language => (
                    <SelectItem key={language.code} value={language.code}>
                      <span className="flex items-center gap-2">
                        <span>{language.flag}</span>
                        <span>{language.name}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* АВАТАР ИЛИ КНОПКИ */}
              <div className="flex items-center">
                {user ? (
                  <motion.div 
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    onClick={() => navigate('/settings')}
                    className="flex items-center gap-2 sm:gap-3 bg-white/5 p-1 sm:p-1.5 pr-2 sm:pr-4 rounded-full border border-white/10 cursor-pointer hover:bg-white/10 transition-all group"
                  >
                    {user.avatar ? (
                      <img 
                        src={user.avatar} 
                        alt={user.username}
                        className="w-7 h-7 sm:w-9 sm:h-9 rounded-full border-2 border-cyber-cyan shadow-[0_0_15px_rgba(0,255,243,0.3)] group-hover:shadow-cyber-cyan/50 transition-all object-cover"
                      />
                    ) : (
                      <div className="w-7 h-7 sm:w-9 sm:h-9 bg-gradient-to-br from-cyber-cyan to-neon-purple rounded-full flex items-center justify-center font-bold text-black border-2 border-cyber-cyan shadow-[0_0_15px_rgba(0,255,243,0.3)] group-hover:shadow-cyber-cyan/50 transition-all text-sm">
                        {(user.display_name || user.username || 'U')[0].toUpperCase()}
                      </div>
                    )}
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
                  <div className="flex items-center gap-1 sm:gap-2 bg-black/20 p-1 rounded-xl border border-white/5">
                    <Button 
                      variant="ghost" 
                      onClick={() => navigate('/auth?mode=login')}
                      className="text-text-main hover:bg-white/10 px-2 sm:px-4 h-7 sm:h-9 text-xs sm:text-sm"
                    >
                      {t('login') || 'Log In'}
                    </Button>
                    <Button 
                      onClick={() => navigate('/auth?mode=register')}
                      className="bg-cyber-cyan text-black hover:bg-cyber-cyan/80 px-3 sm:px-5 h-7 sm:h-9 font-unbounded text-[9px] sm:text-[10px] font-bold rounded-lg shadow-lg shadow-cyber-cyan/20"
                    >
                      {t('playNow') || 'PLAY'}
                    </Button>
                  </div>
                )}
              </div>
            </motion.div>
          </nav>
        </header>

        {/* HERO CONTENT */}
        <main className="container mx-auto px-4 sm:px-6 pt-8 sm:pt-12 pb-16 sm:pb-24">
          <div className="max-w-4xl mx-auto text-center">
            <motion.h1 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              className="font-unbounded text-3xl sm:text-4xl lg:text-6xl font-black text-text-main mb-4 sm:mb-6 leading-tight uppercase"
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
              className="text-base sm:text-lg text-text-muted mb-8 sm:mb-10 max-w-2xl mx-auto px-4"
            >
              {t('description')}
            </motion.p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-12 sm:mb-16 px-4">
              <Button 
                onClick={() => user ? navigate('/game') : navigate('/auth?mode=register')}
                className="w-full sm:w-auto bg-cyber-cyan text-black px-6 sm:px-8 py-6 sm:py-7 font-unbounded text-sm font-bold rounded-2xl shadow-xl shadow-cyber-cyan/20 hover:scale-105 transition-transform"
              >
                {user ? (t('toCity') || 'TO CITY') : (t('startBuilding') || 'START BUILDING')}
              </Button>
              
              <Button 
                variant="outline"
                onClick={() => setShowTutorial(true)}
                className="w-full sm:w-auto border-white/10 bg-white/5 text-white px-6 sm:px-8 py-6 sm:py-7 font-unbounded text-sm hover:bg-white/10"
              >
                <GraduationCap className="w-5 h-5 mr-2 text-neon-purple" />
                {t('tutorial') || 'TUTORIAL'}
              </Button>
            </div>

            {/* СТАТИСТИКА ИГРЫ */}
            {stats && (
              <motion.div 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-16 sm:mb-20"
              >
                {[
                  { label: t('players'), value: stats.total_players, color: 'text-cyber-cyan' },
                  { label: t('plotsBought'), value: stats.owned_plots, color: 'text-cyber-cyan' },
                  { label: t('businesses'), value: stats.total_businesses, color: 'text-cyber-cyan' },
                  { label: t('tonInCirculation'), value: stats.total_volume_ton?.toFixed(1), color: 'text-signal-amber' }
                ].map((s, i) => (
                  <div key={i} className="glass-panel rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-white/5 bg-white/2">
                    <div className={`text-2xl sm:text-3xl font-mono ${s.color} font-bold mb-1`}>{s.value || 0}</div>
                    <div className="text-[9px] sm:text-[10px] text-text-muted uppercase tracking-[0.15em] sm:tracking-[0.2em]">{s.label}</div>
                  </div>
                ))}
              </motion.div>
            )}

            {/* ДАННЫЕ ПОЛЬЗОВАТЕЛЯ (если авторизован) */}
            {user && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="mb-16 sm:mb-20"
              >
                <h2 className="font-unbounded text-lg sm:text-xl font-bold text-white mb-6 uppercase tracking-wide">
                  {t('yourStats') || 'Your Stats'}
                </h2>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 max-w-3xl mx-auto">
                  <div className="glass-panel rounded-xl p-4 sm:p-5 border border-cyber-cyan/20 bg-cyber-cyan/5">
                    <Wallet className="w-5 h-5 text-cyber-cyan mb-2" />
                    <div className="text-xl sm:text-2xl font-mono text-white font-bold">
                      {user.balance_ton?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-[10px] text-text-muted uppercase tracking-wider">TON</div>
                  </div>
                  <div className="glass-panel rounded-xl p-4 sm:p-5 border border-neon-purple/20 bg-neon-purple/5">
                    <Coins className="w-5 h-5 text-neon-purple mb-2" />
                    <div className="text-xl sm:text-2xl font-mono text-white font-bold">
                      {user.balance_game?.toFixed(0) || '0'}
                    </div>
                    <div className="text-[10px] text-text-muted uppercase tracking-wider">{t('coins') || 'Coins'}</div>
                  </div>
                  <div className="glass-panel rounded-xl p-4 sm:p-5 border border-signal-amber/20 bg-signal-amber/5">
                    <Building2 className="w-5 h-5 text-signal-amber mb-2" />
                    <div className="text-xl sm:text-2xl font-mono text-white font-bold">
                      {user.businesses_owned?.length || 0}
                    </div>
                    <div className="text-[10px] text-text-muted uppercase tracking-wider">{t('businesses')}</div>
                  </div>
                  <div className="glass-panel rounded-xl p-4 sm:p-5 border border-green-500/20 bg-green-500/5">
                    <TrendingUp className="w-5 h-5 text-green-400 mb-2" />
                    <div className="text-xl sm:text-2xl font-mono text-white font-bold">
                      {user.level || 1}
                    </div>
                    <div className="text-[10px] text-text-muted uppercase tracking-wider">{t('level')}</div>
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* КАРТОЧКИ ФУНКЦИЙ */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 max-w-6xl mx-auto mb-16 sm:mb-20">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + index * 0.1 }}
                  className="glass-panel group hover:border-cyber-cyan/30 rounded-2xl sm:rounded-3xl p-6 sm:p-8 transition-all relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                    <Icon className="w-16 sm:w-20 h-16 sm:h-20 text-white" />
                  </div>
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-cyber-cyan/10 flex items-center justify-center mb-4 sm:mb-6 border border-cyber-cyan/20">
                    <Icon className="w-5 h-5 sm:w-6 sm:h-6 text-cyber-cyan" />
                  </div>
                  <h3 className="font-unbounded text-base sm:text-lg font-bold text-white mb-2 sm:mb-3 uppercase tracking-tight">
                    {feature.title}
                  </h3>
                  <p className="text-text-muted text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </motion.div>
              );
            })}
          </div>

          {/* КАК ЭТО РАБОТАЕТ - ИНФОРМАЦИЯ О ПРОЕКТЕ */}
          <div className="max-w-6xl mx-auto mb-16 sm:mb-20">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
            >
              <h2 className="font-unbounded text-xl sm:text-2xl lg:text-3xl font-bold text-white text-center mb-4 uppercase tracking-tight">
                <Sparkles className="w-6 h-6 inline-block mr-2 text-cyber-cyan" />
                {t('howItWorks') || 'How It Works'}
              </h2>
              <p className="text-text-muted text-center mb-8 sm:mb-12 max-w-2xl mx-auto">
                {t('howItWorksDesc') || 'TON City Builder is a blockchain-based economic strategy game where you can build your business empire and earn real cryptocurrency.'}
              </p>
              
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                {gameMechanics.map((item, index) => {
                  const Icon = item.icon;
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.9 + index * 0.1 }}
                      className="bg-white/2 border border-white/5 rounded-xl p-5 sm:p-6 hover:border-white/10 transition-all"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-lg bg-cyber-cyan/10 flex items-center justify-center flex-shrink-0">
                          <Icon className="w-5 h-5 text-cyber-cyan" />
                        </div>
                        <div>
                          <h4 className="font-bold text-white mb-1 text-sm sm:text-base">{item.title}</h4>
                          <p className="text-text-muted text-xs sm:text-sm leading-relaxed">{item.desc}</p>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          </div>

          {/* БЛОКЧЕЙН ПРЕИМУЩЕСТВА */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2 }}
            className="max-w-4xl mx-auto text-center mb-16 sm:mb-20"
          >
            <div className="glass-panel rounded-2xl sm:rounded-3xl p-6 sm:p-10 border border-cyber-cyan/10 bg-gradient-to-br from-cyber-cyan/5 to-neon-purple/5">
              <h3 className="font-unbounded text-lg sm:text-xl font-bold text-white mb-4 uppercase">
                {t('poweredByTON') || 'Powered by TON Blockchain'}
              </h3>
              <p className="text-text-muted mb-6 text-sm sm:text-base">
                {t('tonAdvantages') || 'Lightning-fast transactions, minimal fees, and complete ownership of your in-game assets. Your progress and earnings are stored securely on the blockchain.'}
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <div className="bg-white/5 px-4 py-2 rounded-full text-xs sm:text-sm text-cyber-cyan border border-cyber-cyan/20">
                  ⚡ {t('fastTransactions') || 'Fast Transactions'}
                </div>
                <div className="bg-white/5 px-4 py-2 rounded-full text-xs sm:text-sm text-cyber-cyan border border-cyber-cyan/20">
                  💰 {t('lowFees') || 'Low Fees'}
                </div>
                <div className="bg-white/5 px-4 py-2 rounded-full text-xs sm:text-sm text-cyber-cyan border border-cyber-cyan/20">
                  🔒 {t('trueOwnership') || 'True Ownership'}
                </div>
              </div>
            </div>
          </motion.div>
        </main>

        <footer className="border-t border-white/5 py-8 sm:py-12 mt-8 sm:mt-12 bg-black/20">
          <div className="container mx-auto px-4 sm:px-6 text-center">
            <div className="flex items-center justify-center gap-2 mb-4 opacity-50">
              <Building2 className="w-4 h-4 sm:w-5 sm:h-5" />
              <span className="font-unbounded text-[10px] sm:text-xs font-bold uppercase tracking-widest">Ton City Builder</span>
            </div>
            <p className="text-text-muted text-[9px] sm:text-[10px] uppercase tracking-widest">
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
