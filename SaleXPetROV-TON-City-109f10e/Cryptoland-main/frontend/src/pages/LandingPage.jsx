import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TonConnectButton, useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import { motion } from 'framer-motion';
import { Building2, Coins, Users, TrendingUp, Zap, MapPin, Calculator, Globe } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { verifyWallet, getGameStats } from '@/lib/api';
import { useTranslation } from '@/lib/translations';
import { toast } from 'sonner';

export default function LandingPage() {
  const navigate = useNavigate();
  const [tonConnectUI] = useTonConnectUI();
  const wallet = useTonWallet();
  const [stats, setStats] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [lang, setLang] = useState(localStorage.getItem('ton_city_lang') || 'en');
  const { t } = useTranslation(lang);

  const changeLang = (newLang) => {
    setLang(newLang);
    localStorage.setItem('ton_city_lang', newLang);
  };

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    if (wallet?.account) {
      handleWalletConnect();
    }
  }, [wallet?.account]);

  const loadStats = async () => {
    try {
      const data = await getGameStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleWalletConnect = async () => {
    if (!wallet?.account?.address || isVerifying) return;
    
    setIsVerifying(true);
    try {
      await verifyWallet(wallet.account.address, null, lang);
      toast.success(lang === 'ru' ? 'Кошелёк подключен!' : lang === 'zh' ? '钱包已连接!' : 'Wallet connected!');
      navigate('/game');
    } catch (error) {
      console.error('Verification failed:', error);
      toast.error(lang === 'ru' ? 'Ошибка подключения' : 'Connection error');
    } finally {
      setIsVerifying(false);
    }
  };

  const features = [
    {
      icon: MapPin,
      title: t('buyLand'),
      description: t('buyLandDesc'),
    },
    {
      icon: Building2,
      title: t('buildBusiness'),
      description: t('buildBusinessDesc'),
    },
    {
      icon: Zap,
      title: t('createConnections'),
      description: t('createConnectionsDesc'),
    },
    {
      icon: Coins,
      title: t('earnTon'),
      description: t('earnTonDesc'),
    },
  ];

  return (
    <div className="min-h-screen bg-void relative overflow-hidden">
      {/* Background grid effect */}
      <div className="absolute inset-0 opacity-10">
        <div 
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0, 240, 255, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0, 240, 255, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px',
          }}
        />
      </div>

      {/* Hero Section */}
      <div className="relative z-10">
        {/* Header */}
        <header className="container mx-auto px-6 py-6">
          <nav className="flex items-center justify-between">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyber-cyan to-neon-purple flex items-center justify-center">
                <Building2 className="w-6 h-6 text-black" />
              </div>
              <span className="font-unbounded text-xl font-bold text-text-main">
                TON City
              </span>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
              <Select value={lang} onValueChange={changeLang}>
                <SelectTrigger className="w-28 bg-panel border-grid-border text-text-main">
                  <Globe className="w-4 h-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="ru">Русский</SelectItem>
                  <SelectItem value="zh">中文</SelectItem>
                </SelectContent>
              </Select>
              <TonConnectButton />
            </motion.div>
          </nav>
        </header>

        {/* Hero Content */}
        <main className="container mx-auto px-6 pt-12 pb-24">
          <div className="max-w-4xl mx-auto text-center">
            <motion.h1 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="font-unbounded text-4xl sm:text-5xl lg:text-6xl font-black text-text-main mb-6 leading-tight"
            >
              {t('title')}{' '}
              <span className="gradient-text">{t('subtitle')}</span>
            </motion.h1>

            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-lg text-text-muted mb-10 max-w-2xl mx-auto font-rajdhani"
            >
              {t('description')}
            </motion.p>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
            >
              {wallet?.account ? (
                <Button 
                  onClick={() => navigate('/game')}
                  className="btn-cyber px-8 py-6 text-lg rounded-xl"
                  data-testid="play-now-btn"
                >
                  {t('playNow')}
                </Button>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <p className="text-text-muted text-sm">{t('connectToPlay')}</p>
                  <TonConnectButton />
                </div>
              )}
              
              <Button 
                variant="outline"
                onClick={() => navigate('/income-table')}
                className="border-cyber-cyan/30 text-cyber-cyan hover:bg-cyber-cyan/10 px-6 py-5"
              >
                <Calculator className="w-4 h-4 mr-2" />
                {t('incomeTable')}
              </Button>
            </motion.div>

            {/* Stats */}
            {stats && (
              <motion.div 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-20"
              >
                <div className="glass-panel rounded-xl p-6 text-center">
                  <div className="text-3xl font-mono text-cyber-cyan font-bold mb-1">
                    {stats.total_players || 0}
                  </div>
                  <div className="text-sm text-text-muted uppercase tracking-wider">{t('players')}</div>
                </div>
                <div className="glass-panel rounded-xl p-6 text-center">
                  <div className="text-3xl font-mono text-cyber-cyan font-bold mb-1">
                    {stats.owned_plots || 0}
                  </div>
                  <div className="text-sm text-text-muted uppercase tracking-wider">{t('plotsBought')}</div>
                </div>
                <div className="glass-panel rounded-xl p-6 text-center">
                  <div className="text-3xl font-mono text-cyber-cyan font-bold mb-1">
                    {stats.total_businesses || 0}
                  </div>
                  <div className="text-sm text-text-muted uppercase tracking-wider">{t('businesses')}</div>
                </div>
                <div className="glass-panel rounded-xl p-6 text-center">
                  <div className="text-3xl font-mono text-signal-amber font-bold mb-1">
                    {(stats.total_volume_ton || 0).toFixed(1)}
                  </div>
                  <div className="text-sm text-text-muted uppercase tracking-wider">{t('tonInCirculation')}</div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Features */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto"
          >
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                className="glass-panel glass-panel-hover rounded-2xl p-6 relative corner-brackets"
              >
                <div className="w-12 h-12 rounded-lg bg-cyber-cyan-dim flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-cyber-cyan" />
                </div>
                <h3 className="font-unbounded text-lg font-bold text-text-main mb-2">
                  {feature.title}
                </h3>
                <p className="text-text-muted text-sm font-rajdhani">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </motion.div>

          {/* Business Types Preview */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="mt-24 max-w-4xl mx-auto"
          >
            <h2 className="font-unbounded text-2xl font-bold text-center text-text-main mb-8">
              {t('businessTypes')}
            </h2>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
              {[
                { icon: '🌾', name: lang === 'ru' ? 'Ферма' : lang === 'zh' ? '农场' : 'Farm', cost: 5 },
                { icon: '🏭', name: lang === 'ru' ? 'Завод' : lang === 'zh' ? '工厂' : 'Factory', cost: 15 },
                { icon: '🏪', name: lang === 'ru' ? 'Магазин' : lang === 'zh' ? '商店' : 'Shop', cost: 10 },
                { icon: '⚡', name: lang === 'ru' ? 'Энергия' : lang === 'zh' ? '发电厂' : 'Power', cost: 20 },
                { icon: '🏦', name: lang === 'ru' ? 'Банк' : lang === 'zh' ? '银行' : 'Bank', cost: 50 },
                { icon: '📊', name: lang === 'ru' ? 'Биржа' : lang === 'zh' ? '交易所' : 'Exchange', cost: 100 },
              ].map((biz) => (
                <div 
                  key={biz.name}
                  className="glass-panel rounded-xl p-4 text-center card-hover"
                >
                  <div className="text-4xl mb-2">{biz.icon}</div>
                  <div className="text-sm text-text-main font-rajdhani font-semibold">{biz.name}</div>
                  <div className="text-xs text-cyber-cyan font-mono">{biz.cost} TON</div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* How it works */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 }}
            className="mt-24 max-w-3xl mx-auto text-center"
          >
            <h2 className="font-unbounded text-2xl font-bold text-text-main mb-6">
              {t('howEconomyWorks')}
            </h2>
            <div className="glass-panel rounded-2xl p-8">
              <div className="flex flex-col md:flex-row items-center justify-center gap-4 text-lg">
                <div className="flex items-center gap-2">
                  <span className="text-3xl">🌾</span>
                  <span className="text-text-muted">{lang === 'ru' ? 'Ферма' : 'Farm'}</span>
                </div>
                <span className="text-cyber-cyan text-2xl">→</span>
                <div className="flex items-center gap-2">
                  <span className="text-3xl">🏭</span>
                  <span className="text-text-muted">{lang === 'ru' ? 'Завод' : 'Factory'}</span>
                </div>
                <span className="text-cyber-cyan text-2xl">→</span>
                <div className="flex items-center gap-2">
                  <span className="text-3xl">🏪</span>
                  <span className="text-text-muted">{lang === 'ru' ? 'Магазин' : 'Shop'}</span>
                </div>
                <span className="text-signal-amber text-2xl">→</span>
                <div className="flex items-center gap-2">
                  <span className="text-3xl">💰</span>
                  <span className="text-signal-amber font-bold">TON</span>
                </div>
              </div>
              <p className="text-text-muted mt-6 font-rajdhani">
                {t('economyDesc')}
              </p>
            </div>
          </motion.div>
        </main>

        {/* Footer */}
        <footer className="border-t border-grid-border py-8">
          <div className="container mx-auto px-6 text-center text-text-muted text-sm">
            <p>TON City Builder © 2025. Построено на блокчейне TON.</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
