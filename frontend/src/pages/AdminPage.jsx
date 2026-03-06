import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTonWallet } from '@tonconnect/ui-react';
import { motion } from 'framer-motion';
import { 
  Users, Building2, DollarSign, TrendingUp, Settings, 
  CreditCard, Bell, Gift, RefreshCw, Check, X, ArrowLeft, Wallet, Copy,
  Wrench, Play, Clock, Home, Calendar
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { useTranslation } from '@/lib/translations';
import { toast } from 'sonner';
import axios from 'axios';
import WalletSettings from '@/components/WalletSettings';
import RevenueAnalytics from '@/components/RevenueAnalytics';
import TreasuryWarning from '@/components/TreasuryWarning';
import AdminDataPanel from '@/components/AdminDataPanel';
import { toUserFriendlyAddress } from '@/lib/tonAddress';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminPage({ user }) {
  const navigate = useNavigate();
  const wallet = useTonWallet();
  const [lang, setLang] = useState(localStorage.getItem('ton_city_lang') || 'en');
  const { t } = useTranslation(lang);
  
  const [stats, setStats] = useState(null);
  const [treasuryHealth, setTreasuryHealth] = useState(null);
  const [users, setUsers] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [promos, setPromos] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  
  // Maintenance states
  const [maintenanceEnabled, setMaintenanceEnabled] = useState(false);
  const [showMaintenanceDialog, setShowMaintenanceDialog] = useState(false);
  const [scheduledTime, setScheduledTime] = useState('');
  
  // Form states
  const [promoName, setPromoName] = useState('');
  const [promoAmount, setPromoAmount] = useState('');
  const [promoMaxUses, setPromoMaxUses] = useState('');
  const [promoCode, setPromoCode] = useState('');
  const [announcementTitle, setAnnouncementTitle] = useState('');
  const [announcementMessage, setAnnouncementMessage] = useState('');
  
  // Credit admin states
  const [credits, setCredits] = useState([]);
  const [creditSettings, setCreditSettings] = useState({ government_interest_rate: 0.15 });
  const [govRate, setGovRate] = useState('15');
  
  // Withdrawal selection states
  const [selectedWithdrawals, setSelectedWithdrawals] = useState(new Set());
  const [selectAllWithdrawals, setSelectAllWithdrawals] = useState(false);
  
  // Admin wallet settings
  const [walletConfigs, setWalletConfigs] = useState([]);
  const [newWallet, setNewWallet] = useState({ address: '', percentage: 100, mnemonic: '' });
  const [showWalletModal, setShowWalletModal] = useState(false);
  
  // Tax settings
  const [taxSettings, setTaxSettings] = useState({
    small_business_tax: 5,
    medium_business_tax: 8,
    large_business_tax: 10,
    land_business_sale_tax: 10
  });
  
  // User details
  const [userDetailId, setUserDetailId] = useState('');
  const [userDetail, setUserDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  
  // Telegram bot
  const [telegramBotToken, setTelegramBotToken] = useState('');
  const [settingWebhook, setSettingWebhook] = useState(false);
  const token = localStorage.getItem('ton_city_token') || localStorage.getItem('token');

  useEffect(() => {
    if (!token) {
      navigate('/');
      return;
    }
    checkAdmin();
  }, [token]);

  const checkAdmin = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!response.data.is_admin) {
        toast.error('Admin access required');
        navigate('/');
        return;
      }
      
      setIsAdmin(true);
      loadData();
      loadMaintenanceStatus();
    } catch (error) {
      console.error('Admin check failed:', error);
      navigate('/');
    }
  };

  const loadMaintenanceStatus = async () => {
    try {
      const response = await axios.get(`${API}/admin/maintenance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMaintenanceEnabled(response.data.enabled || false);
    } catch (error) {
      console.error('Failed to load maintenance status:', error);
    }
  };

  const toggleMaintenance = async (startNow = false, scheduledAt = null) => {
    try {
      const newState = !maintenanceEnabled;
      await axios.post(`${API}/admin/maintenance`, {
        enabled: newState,
        scheduled_at: startNow ? null : scheduledAt
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMaintenanceEnabled(newState);
      setShowMaintenanceDialog(false);
      
      if (newState) {
        toast.success(startNow ? 'Технические работы начаты' : 'Технические работы запланированы');
      } else {
        toast.success('Технические работы завершены');
      }
    } catch (error) {
      console.error('Failed to toggle maintenance:', error);
      toast.error('Ошибка при изменении статуса');
    }
  };

  const loadData = async () => {
    setIsLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      const [statsRes, usersRes, txRes, promosRes, announcementsRes, treasuryRes, creditsRes, creditSettingsRes, taxRes, walletsRes] = await Promise.all([
        axios.get(`${API}/admin/stats`, { headers }),
        axios.get(`${API}/admin/users?limit=50`, { headers }),
        axios.get(`${API}/admin/transactions?limit=100`, { headers }),
        axios.get(`${API}/admin/promos`, { headers }).catch(() => ({ data: { promos: [] } })),
        axios.get(`${API}/admin/announcements`, { headers }).catch(() => ({ data: { announcements: [] } })),
        axios.get(`${API}/admin/treasury-health`, { headers }).catch(() => ({ data: {} })),
        axios.get(`${API}/admin/credits`, { headers }).catch(() => ({ data: { credits: [] } })),
        axios.get(`${API}/admin/credit-settings`, { headers }).catch(() => ({ data: { government_interest_rate: 0.15 } })),
        axios.get(`${API}/admin/settings/tax`, { headers }).catch(() => ({ data: { land_market_tax: 10, resource_market_tax: 5, business_upgrade_tax: 3 } })),
        axios.get(`${API}/admin/wallets`, { headers }).catch(() => ({ data: { wallets: [] } })),
      ]);
      
      setStats(statsRes.data);
      setUsers(usersRes.data.users || []);
      setTransactions(txRes.data.transactions || []);
      setPromos(promosRes.data.promos || []);
      setAnnouncements(announcementsRes.data.announcements || []);
      setTreasuryHealth(treasuryRes.data);
      setCredits(creditsRes.data.credits || []);
      if (creditSettingsRes.data) {
        setCreditSettings(creditSettingsRes.data);
        setGovRate(((creditSettingsRes.data.government_interest_rate || 0.15) * 100).toFixed(0));
      }
      if (taxRes.data) {
        setTaxSettings(taxRes.data);
      }
      if (walletsRes.data) {
        setWalletConfigs(walletsRes.data.wallets || []);
      }
    } catch (error) {
      console.error('Failed to load admin data:', error);
      toast.error('Failed to load data');
    } finally {
      setIsLoading(false);
    }
  };

  const approveWithdrawal = async (txId) => {
    try {
      await axios.post(`${API}/admin/withdrawal/approve/${txId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Withdrawal approved');
      setSelectedWithdrawals(prev => {
        const newSet = new Set(prev);
        newSet.delete(txId);
        return newSet;
      });
      loadData();
    } catch (error) {
      const msg = error.response?.data?.detail || 'Failed to approve';
      toast.error(msg);
    }
  };

  const rejectWithdrawal = async (txId) => {
    try {
      await axios.post(`${API}/admin/withdrawal/reject/${txId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Withdrawal rejected and refunded');
      setSelectedWithdrawals(prev => {
        const newSet = new Set(prev);
        newSet.delete(txId);
        return newSet;
      });
      loadData();
    } catch (error) {
      toast.error('Failed to reject');
    }
  };

  // Bulk withdrawal actions
  const handleSelectAllWithdrawals = (checked) => {
    setSelectAllWithdrawals(checked);
    if (checked) {
      setSelectedWithdrawals(new Set(pendingWithdrawals.map(tx => tx.id)));
    } else {
      setSelectedWithdrawals(new Set());
    }
  };

  const toggleWithdrawalSelection = (txId) => {
    setSelectedWithdrawals(prev => {
      const newSet = new Set(prev);
      if (newSet.has(txId)) {
        newSet.delete(txId);
      } else {
        newSet.add(txId);
      }
      return newSet;
    });
  };

  const bulkApproveWithdrawals = async () => {
    if (selectedWithdrawals.size === 0) {
      toast.error('Выберите заявки для одобрения');
      return;
    }
    
    let success = 0;
    let failed = 0;
    
    for (const txId of selectedWithdrawals) {
      try {
        await axios.post(`${API}/admin/withdrawal/approve/${txId}`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        success++;
      } catch {
        failed++;
      }
    }
    
    toast.success(`Одобрено: ${success}, Ошибок: ${failed}`);
    setSelectedWithdrawals(new Set());
    setSelectAllWithdrawals(false);
    loadData();
  };

  const bulkRejectWithdrawals = async () => {
    if (selectedWithdrawals.size === 0) {
      toast.error('Выберите заявки для отклонения');
      return;
    }
    
    let success = 0;
    let failed = 0;
    
    for (const txId of selectedWithdrawals) {
      try {
        await axios.post(`${API}/admin/withdrawal/reject/${txId}`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        success++;
      } catch {
        failed++;
      }
    }
    
    toast.success(`Отклонено и возвращено: ${success}, Ошибок: ${failed}`);
    setSelectedWithdrawals(new Set());
    setSelectAllWithdrawals(false);
    loadData();
  };

  // Tax settings
  const saveTaxSettings = async () => {
    try {
      await axios.post(`${API}/admin/settings/tax`, taxSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Налоговые настройки сохранены');
    } catch (error) {
      toast.error('Ошибка сохранения налогов');
    }
  };

  // User resource update
  const updateUserResources = async (userId, resources) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/resources`, { resources }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Ресурсы пользователя обновлены');
    } catch (error) {
      toast.error('Ошибка обновления ресурсов');
    }
  };

  const createPromo = async () => {
    try {
      await axios.post(`${API}/admin/promo/create`, null, {
        params: { name: promoName, amount: parseFloat(promoAmount), max_uses: parseInt(promoMaxUses) },
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Promo created');
      setPromoName('');
      setPromoAmount('');
      setPromoMaxUses('');
      loadData();
    } catch (error) {
      toast.error('Failed to create promo');
    }
  };

  const createAnnouncement = async () => {
    try {
      await axios.post(`${API}/admin/announcement`, null, {
        params: { title: announcementTitle, message: announcementMessage, lang: 'all' },
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Announcement created');
      setAnnouncementTitle('');
      setAnnouncementMessage('');
      loadData();
    } catch (error) {
      toast.error('Failed to create announcement');
    }
  };

  const setUserAdmin = async (walletAddress, isAdminStatus) => {
    try {
      await axios.post(`${API}/admin/user/set-admin/${walletAddress}`, null, {
        params: { is_admin: isAdminStatus },
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Admin status ${isAdminStatus ? 'granted' : 'revoked'}`);
      loadData();
    } catch (error) {
      toast.error('Failed to update admin status');
    }
  };

  // Credit admin actions
  const handleUpdateGovRate = async () => {
    try {
      const rate = parseFloat(govRate) / 100;
      await axios.post(`${API}/admin/credit-settings?government_interest_rate=${rate}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Ставка обновлена: ${govRate}%`);
      loadData();
    } catch (e) { toast.error('Ошибка обновления'); }
  };

  const handleCreatePromo = async () => {
    if (!promoName || !promoAmount) {
      toast.error('Заполните название и сумму');
      return;
    }
    try {
      await axios.post(`${API}/admin/promo/create`, {
        name: promoName,
        code: promoCode || promoName.toUpperCase().replace(/\s/g, ''),
        amount: parseFloat(promoAmount),
        max_uses: parseInt(promoMaxUses) || 100,
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Промокод создан');
      setPromoName('');
      setPromoAmount('');
      setPromoMaxUses('');
      setPromoCode('');
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Ошибка'); }
  };

  const handleLoadUserDetail = async () => {
    if (!userDetailId.trim()) return;
    setLoadingDetail(true);
    setUserDetail(null);
    try {
      const res = await axios.get(`${API}/admin/user-details/${encodeURIComponent(userDetailId.trim())}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUserDetail(res.data);
    } catch (e) { toast.error(e.response?.data?.detail || 'Пользователь не найден'); }
    finally { setLoadingDetail(false); }
  };

  const handleSetTelegramWebhook = async () => {
    if (!telegramBotToken.trim()) {
      toast.error('Введите токен бота');
      return;
    }
    setSettingWebhook(true);
    try {
      const res = await axios.post(`${API}/admin/telegram/set-webhook?bot_token=${encodeURIComponent(telegramBotToken.trim())}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Webhook установлен: ${res.data.url}`);
    } catch (e) { toast.error(e.response?.data?.detail || 'Ошибка установки'); }
    finally { setSettingWebhook(false); }
  };

  const AddressDisplay = ({ address, short = false }) => {
    if (!address) return <span className="text-text-muted">-</span>;
  
    // Если адрес уже в user-friendly формате (UQ... или EQ...), используем его напрямую
    // Если это raw адрес (0:...), тогда преобразуем
    let displayAddress = address;
  
    // Проверяем, является ли это raw адресом
    if (address.startsWith('0:') || address.startsWith('-1:')) {
      // Только в этом случае преобразуем
      displayAddress = toUserFriendlyAddress(address);
    }
    // Иначе используем адрес как есть (он уже user-friendly из API)
  
    const copyToClipboard = () => {
      navigator.clipboard.writeText(displayAddress);
      toast.success('Адрес скопирован');
    };
  
    const shortAddress = short 
      ? `${displayAddress.slice(0, 8)}...${displayAddress.slice(-6)}` 
      : displayAddress;
  
    return (
      <div className="flex items-center gap-2 group">
        <span className="font-mono text-sm break-all" title={displayAddress}>
          {shortAddress}
        </span>
        <Button
          variant="ghost"
          size="icon"
          onClick={copyToClipboard}
          className="h-6 w-6 opacity-50 hover:opacity-100"
        >
          <Copy className="w-3 h-3" />
        </Button>
      </div>
    );
  };

  const formatAddress = (address) => {
    if (!address) return '-';
    const friendly = toUserFriendlyAddress(address);
    return `${friendly.slice(0, 8)}...${friendly.slice(-6)}`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  if (isLoading || !isAdmin) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  const pendingWithdrawals = transactions.filter(tx => tx.tx_type === 'withdrawal' && tx.status === 'pending');

  return (
    <div className="min-h-screen bg-void">
      {/* Header */}
      <header className="glass-panel border-b border-grid-border px-4 lg:px-6 py-4">
        <div className="container mx-auto flex flex-wrap items-center justify-between gap-4 pl-12 lg:pl-0">
          <div className="flex items-center gap-2 lg:gap-4">
            <Button
              data-testid="admin-go-to-user-ui"
              variant="ghost"
              size="sm"
              onClick={() => navigate('/')}
              className="text-text-muted hover:text-text-main"
            >
              <Home className="w-4 h-4 lg:mr-2" />
              <span className="hidden lg:inline">На сайт</span>
            </Button>
            <h1 className="font-unbounded text-lg lg:text-xl font-bold text-text-main flex items-center gap-2">
              <Settings className="w-5 h-5 text-cyber-cyan" />
              <span className="hidden sm:inline">{t('adminPanel')}</span>
              <span className="sm:hidden">Админ</span>
            </h1>
          </div>
          
          <div className="flex items-center gap-2 lg:gap-3">
            {/* Maintenance Button */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  data-testid="maintenance-toggle-btn"
                  variant="outline"
                  size="sm"
                  className={`transition-all ${
                    maintenanceEnabled 
                      ? 'bg-orange-500/20 border-orange-500 text-orange-400 hover:bg-orange-500/30' 
                      : 'border-grid-border hover:border-white/30'
                  }`}
                >
                  <Wrench className="w-4 h-4 lg:mr-2" />
                  <span className="hidden lg:inline">
                    {maintenanceEnabled ? 'Тех. работы (ВКЛ)' : 'Тех. работы'}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="bg-panel border-grid-border w-56">
                {!maintenanceEnabled ? (
                  <>
                    <DropdownMenuItem 
                      onClick={() => toggleMaintenance(true)}
                      className="cursor-pointer"
                    >
                      <Play className="w-4 h-4 mr-2 text-orange-400" />
                      Начать прямо сейчас
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      onClick={() => setShowMaintenanceDialog(true)}
                      className="cursor-pointer"
                    >
                      <Clock className="w-4 h-4 mr-2 text-blue-400" />
                      Установить время начала
                    </DropdownMenuItem>
                  </>
                ) : (
                  <DropdownMenuItem 
                    onClick={() => toggleMaintenance(false)}
                    className="cursor-pointer"
                  >
                    <Check className="w-4 h-4 mr-2 text-green-400" />
                    Закончить тех. работы
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
            
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              className="border-grid-border"
            >
              <RefreshCw className="w-4 h-4 lg:mr-2" />
              <span className="hidden lg:inline">{t('refresh')}</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Schedule Maintenance Dialog */}
      <Dialog open={showMaintenanceDialog} onOpenChange={setShowMaintenanceDialog}>
        <DialogContent className="glass-panel border-grid-border">
          <DialogHeader>
            <DialogTitle className="text-text-main flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-400" />
              Запланировать технические работы
            </DialogTitle>
            <DialogDescription className="text-text-muted">
              Укажите дату и время начала технических работ
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              type="datetime-local"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
              className="bg-panel border-grid-border text-text-main"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMaintenanceDialog(false)}>
              Отмена
            </Button>
            <Button 
              onClick={() => toggleMaintenance(false, scheduledTime ? new Date(scheduledTime).toISOString() : null)}
              className="bg-blue-600 hover:bg-blue-700"
              disabled={!scheduledTime}
            >
              Запланировать
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel rounded-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-signal-amber/10 flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-signal-amber" />
              </div>
              <span className="text-text-muted text-sm">{t('totalPlotSales')}</span>
            </div>
            <div className="font-mono text-3xl text-signal-amber">
              {(stats?.treasury?.total_plot_sales || 0).toFixed(2)} TON
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-panel rounded-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-success" />
              </div>
              <span className="text-text-muted text-sm">{t('totalTax')}</span>
            </div>
            <div className="font-mono text-3xl text-success">
              {(stats?.treasury?.total_tax || 0).toFixed(2)} TON
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-panel rounded-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-error/10 flex items-center justify-center">
                <CreditCard className="w-5 h-5 text-error" />
              </div>
              <span className="text-text-muted text-sm">{t('pendingWithdrawals')}</span>
            </div>
            <div className="font-mono text-3xl text-error">
              {stats?.pending_withdrawals || 0}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-panel rounded-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-cyber-cyan/10 flex items-center justify-center">
                <Users className="w-5 h-5 text-cyber-cyan" />
              </div>
              <span className="text-text-muted text-sm">{t('activeUsers')}</span>
            </div>
            <div className="font-mono text-3xl text-cyber-cyan">
              {stats?.active_users_7d || 0} / {stats?.total_users || 0}
            </div>
          </motion.div>
        </div>

        {/* Treasury Health Warning */}
        {treasuryHealth && (
          <TreasuryWarning treasuryStats={treasuryHealth} lang={lang} />
        )}

        {/* Tabs */}
        <Tabs defaultValue="wallet" className="space-y-6">
          <TabsList className="glass-panel border-grid-border flex-wrap">
            <TabsTrigger value="wallet" className="data-[state=active]:bg-cyber-cyan/10 data-[state=active]:text-cyber-cyan">
              <Wallet className="w-4 h-4 mr-2" />
              TON Кошелек
            </TabsTrigger>
            <TabsTrigger value="revenue" className="data-[state=active]:bg-cyber-cyan/10 data-[state=active]:text-cyber-cyan">
              <DollarSign className="w-4 h-4 mr-2" />
              Доходы
            </TabsTrigger>
            <TabsTrigger value="withdrawals" className="data-[state=active]:bg-cyber-cyan/10 data-[state=active]:text-cyber-cyan">
              {t('pendingWithdrawals')} ({pendingWithdrawals.length})
            </TabsTrigger>
            <TabsTrigger value="users" className="data-[state=active]:bg-cyber-cyan/10 data-[state=active]:text-cyber-cyan">
              {t('users')}
            </TabsTrigger>
            <TabsTrigger value="transactions" className="data-[state=active]:bg-cyber-cyan/10 data-[state=active]:text-cyber-cyan">
              {t('transactions')}
            </TabsTrigger>
            <TabsTrigger value="promos" className="data-[state=active]:bg-cyber-cyan/10 data-[state=active]:text-cyber-cyan">
              Promos
            </TabsTrigger>
            <TabsTrigger value="announcements" className="data-[state=active]:bg-cyber-cyan/10 data-[state=active]:text-cyber-cyan">
              {t('announcements')}
            </TabsTrigger>
            <TabsTrigger value="data" className="data-[state=active]:bg-amber-500/10 data-[state=active]:text-amber-400">
              Данные
            </TabsTrigger>
            <TabsTrigger value="credits" className="data-[state=active]:bg-orange-500/10 data-[state=active]:text-orange-400">
              Кредиты
            </TabsTrigger>
            <TabsTrigger value="userdetails" className="data-[state=active]:bg-purple-500/10 data-[state=active]:text-purple-400">
              Детали
            </TabsTrigger>
            <TabsTrigger value="taxes" className="data-[state=active]:bg-red-500/10 data-[state=active]:text-red-400">
              Налоги
            </TabsTrigger>
          </TabsList>

          {/* TON Wallet Tab */}
          <TabsContent value="wallet">
            <WalletSettings token={token} />
          </TabsContent>
          
          {/* Revenue Analytics Tab */}
          <TabsContent value="revenue">
            <RevenueAnalytics token={token} />
          </TabsContent>

          {/* Withdrawals Tab */}
          <TabsContent value="withdrawals">
            <div className="glass-panel rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-unbounded text-lg font-bold text-text-main">
                  {t('pendingWithdrawals')} ({pendingWithdrawals.length})
                </h2>
                
                {pendingWithdrawals.length > 0 && (
                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 text-sm text-text-muted cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={selectAllWithdrawals}
                        onChange={(e) => handleSelectAllWithdrawals(e.target.checked)}
                        className="w-4 h-4 rounded border-white/20 bg-white/5"
                      />
                      Выбрать все
                    </label>
                    
                    {selectedWithdrawals.size > 0 && (
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={bulkApproveWithdrawals}
                          className="bg-success hover:bg-success/80"
                        >
                          <Check className="w-4 h-4 mr-1" />
                          Одобрить ({selectedWithdrawals.size})
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={bulkRejectWithdrawals}
                        >
                          <X className="w-4 h-4 mr-1" />
                          Отклонить ({selectedWithdrawals.size})
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              {pendingWithdrawals.length === 0 ? (
                <div className="text-center py-12 text-text-muted">
                  No pending withdrawals
                </div>
              ) : (
                <ScrollArea className="h-[500px]">
                  <div className="space-y-4">
                    {pendingWithdrawals.map((tx) => (
                      <div
                        key={tx.id}
                        className={`glass-panel rounded-lg p-4 transition-all ${selectedWithdrawals.has(tx.id) ? 'ring-2 ring-cyber-cyan' : ''}`}
                      >
                        <div className="flex items-start gap-4">
                          <input 
                            type="checkbox" 
                            checked={selectedWithdrawals.has(tx.id)}
                            onChange={() => toggleWithdrawalSelection(tx.id)}
                            className="w-5 h-5 mt-2 rounded border-white/20 bg-white/5 cursor-pointer"
                          />
                          <div className="flex-1 space-y-2">
                            <div>
                              <div className="text-xs text-text-muted mb-1">Пользователь:</div>
                              <div className="text-white text-sm">{tx.user_username || tx.user_id}</div>
                            </div>
                            <div>
                              <div className="text-xs text-text-muted mb-1">Куда (To):</div>
                              <AddressDisplay address={tx.to_address_display || tx.to_address} />
                            </div>
                            <div className="text-xs text-text-muted">
                              {formatDate(tx.created_at)}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-mono text-2xl text-signal-amber">
                              {tx.amount_ton} TON
                            </div>
                            <div className="text-sm text-text-muted">
                              Комиссия: {tx.commission} TON
                            </div>
                            <div className="text-sm text-success">
                              К выплате: {(tx.amount_ton - (tx.commission || 0)).toFixed(2)} TON
                            </div>
                          </div>
                          <div className="flex flex-col gap-2">
                            <Button
                              size="sm"
                              onClick={() => approveWithdrawal(tx.id)}
                              className="bg-success hover:bg-success/80"
                            >
                              <Check className="w-4 h-4 mr-1" />
                              Одобрить
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => rejectWithdrawal(tx.id)}
                            >
                              <X className="w-4 h-4 mr-1" />
                              Отклонить
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </div>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users">
            <div className="glass-panel rounded-2xl p-6">
              <h2 className="font-unbounded text-lg font-bold text-text-main mb-6">
                {t('users')} ({users.length})
              </h2>
              
              <ScrollArea className="h-96">
                <div className="space-y-3">
                  {users.map((user) => (
                    <div
                      key={user.wallet_address}
                      className="glass-panel rounded-lg p-4 flex items-center gap-4"
                    >
                      <div className="flex-1">
                        <div className="font-mono text-sm text-text-main flex items-center gap-2">
                          {formatAddress(user.wallet_address)}
                          {user.is_admin && (
                            <span className="px-2 py-0.5 bg-cyber-cyan/20 text-cyber-cyan text-xs rounded">
                              ADMIN
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-text-muted">
                          Level: {user.level} | Plots: {user.plots_owned?.length || 0} | Businesses: {user.businesses_owned?.length || 0}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono text-sm text-success">
                          {(user.total_income || 0).toFixed(2)} TON income
                        </div>
                        <div className="text-xs text-text-muted">
                          Balance: {(user.balance_ton || 0).toFixed(2)} TON
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant={user.is_admin ? "destructive" : "outline"}
                        onClick={() => setUserAdmin(user.wallet_address, !user.is_admin)}
                      >
                        {user.is_admin ? 'Remove Admin' : 'Make Admin'}
                      </Button>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </TabsContent>

          {/* Transactions Tab */}
          <TabsContent value="transactions">
            <div className="glass-panel rounded-2xl p-6">
              <h2 className="font-unbounded text-lg font-bold text-text-main mb-6">
                {t('transactions')}
              </h2>
              
              <ScrollArea className="h-96">
                <div className="space-y-2">
                  {transactions.map((tx) => (
                    <div
                      key={tx.id}
                      className="glass-panel rounded-lg p-3 flex items-center gap-4 text-sm"
                    >
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        tx.status === 'completed' ? 'bg-success/20 text-success' :
                        tx.status === 'pending' ? 'bg-signal-amber/20 text-signal-amber' :
                        'bg-error/20 text-error'
                      }`}>
                        {tx.status}
                      </span>
                      <span className="text-text-muted">{tx.tx_type}</span>
                      <span className="font-mono text-text-main flex-1">
                        {formatAddress(tx.from_address)} → {formatAddress(tx.to_address)}
                      </span>
                      <span className="font-mono text-signal-amber">
                        {tx.amount_ton} TON
                      </span>
                      <span className="text-text-muted text-xs">
                        {formatDate(tx.created_at)}
                      </span>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </TabsContent>

          {/* Promos Tab */}
          <TabsContent value="promos">
            <div className="space-y-6">
              {/* Promo code creation */}
              <div className="glass-panel rounded-xl p-4 border border-green-500/20">
                <h3 className="font-unbounded text-sm font-bold text-white mb-3">Создать промокод</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                  <Input
                    data-testid="promo-name-input"
                    placeholder="Название"
                    value={promoName}
                    onChange={(e) => setPromoName(e.target.value)}
                    className="bg-white/5 border-white/10"
                  />
                  <Input
                    data-testid="promo-code-input"
                    placeholder="Код (авто)"
                    value={promoCode}
                    onChange={(e) => setPromoCode(e.target.value)}
                    className="bg-white/5 border-white/10"
                  />
                  <Input
                    data-testid="promo-amount-input"
                    type="number"
                    step="0.01"
                    placeholder="Сумма TON"
                    value={promoAmount}
                    onChange={(e) => setPromoAmount(e.target.value)}
                    className="bg-white/5 border-white/10"
                  />
                  <Input
                    type="number"
                    placeholder="Макс. использований"
                    value={promoMaxUses}
                    onChange={(e) => setPromoMaxUses(e.target.value)}
                    className="bg-white/5 border-white/10"
                  />
                </div>
                <Button data-testid="create-promo-btn" onClick={handleCreatePromo} className="btn-cyber">
                  <Gift className="w-4 h-4 mr-1" /> Создать промокод
                </Button>
              </div>

              {/* Existing promos */}
              <div className="glass-panel rounded-xl p-4 border border-white/10">
                <h3 className="font-unbounded text-sm font-bold text-white mb-3">Промокоды ({promos.length})</h3>
                <p className="text-xs text-text-muted mb-3">Каждый пользователь может использовать промокод только 1 раз</p>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {promos.map(p => (
                    <div key={p.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg text-sm">
                      <div>
                        <div className="font-mono text-cyber-cyan font-bold">{p.code || p.name}</div>
                        <div className="text-text-muted text-xs">{p.name}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-signal-amber font-bold">{p.amount} TON</div>
                        <div className="text-xs text-text-muted">Использовано: {p.current_uses || 0}/{p.max_uses || '∞'}</div>
                      </div>
                    </div>
                  ))}
                  {promos.length === 0 && (
                    <p className="text-text-muted text-center py-4">Нет промокодов</p>
                  )}
                </div>
              </div>

              {/* Telegram Bot Settings */}
              <div className="glass-panel rounded-xl p-4 border border-[#26A5E4]/20">
                <h3 className="font-unbounded text-sm font-bold text-white mb-3">Telegram бот</h3>
                <p className="text-text-muted text-xs mb-3">Введите токен бота от @BotFather для уведомлений</p>
                <div className="flex gap-2">
                  <Input
                    data-testid="telegram-bot-token"
                    type="password"
                    placeholder="Bot token..."
                    value={telegramBotToken}
                    onChange={(e) => setTelegramBotToken(e.target.value)}
                    className="bg-white/5 border-white/10"
                  />
                  <Button onClick={handleSetTelegramWebhook} disabled={settingWebhook} className="bg-[#26A5E4] text-white">
                    {settingWebhook ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Установить'}
                  </Button>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Announcements Tab */}
          <TabsContent value="announcements">
            <div className="glass-panel rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-unbounded text-lg font-bold text-text-main">
                  {t('announcements')}
                </h2>
                
                <Dialog>
                  <DialogTrigger asChild>
                    <Button className="btn-cyber">
                      <Bell className="w-4 h-4 mr-2" />
                      {t('createAnnouncement')}
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="glass-panel border-grid-border text-text-main">
                    <DialogHeader>
                      <DialogTitle>Create Announcement</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <Input
                        placeholder="Title"
                        value={announcementTitle}
                        onChange={(e) => setAnnouncementTitle(e.target.value)}
                        className="bg-panel border-grid-border"
                      />
                      <textarea
                        placeholder="Message"
                        value={announcementMessage}
                        onChange={(e) => setAnnouncementMessage(e.target.value)}
                        className="w-full h-32 bg-panel border border-grid-border rounded-lg p-3 text-text-main"
                      />
                      <Button onClick={createAnnouncement} className="w-full btn-cyber">
                        Create & Broadcast
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
              
              <div className="space-y-3">
                {announcements.map((ann) => (
                  <div
                    key={ann.id}
                    className="glass-panel rounded-lg p-4"
                  >
                    <div className="font-unbounded text-text-main mb-2">
                      {ann.title}
                    </div>
                    <div className="text-text-muted text-sm mb-2">
                      {ann.message}
                    </div>
                    <div className="text-xs text-text-muted">
                      {formatDate(ann.created_at)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* DATA TAB - Players & Prices */}
          <TabsContent value="data">
            <AdminDataPanel token={token} />
          </TabsContent>

          {/* CREDITS TAB */}
          <TabsContent value="credits">
            <div className="space-y-6">
              {/* Government rate settings */}
              <div className="glass-panel rounded-xl p-4 border border-amber-500/20">
                <h3 className="font-unbounded text-sm font-bold text-white mb-3">Ставка государственного кредита</h3>
                <div className="flex items-center gap-3">
                  <Input
                    data-testid="gov-rate-input"
                    type="number"
                    min="1"
                    max="100"
                    value={govRate}
                    onChange={(e) => setGovRate(e.target.value)}
                    className="w-24 bg-white/5 border-white/10"
                    placeholder="%"
                  />
                  <span className="text-text-muted">%</span>
                  <Button onClick={handleUpdateGovRate} size="sm" className="btn-cyber">
                    <Check className="w-4 h-4 mr-1" /> Сохранить
                  </Button>
                  <span className="text-text-muted text-xs">Текущая: {(creditSettings.government_interest_rate * 100).toFixed(0)}%</span>
                </div>
              </div>

              {/* Active credits with FULL user ID */}
              <div className="glass-panel rounded-xl p-4 border border-white/10">
                <h3 className="font-unbounded text-sm font-bold text-white mb-3">
                  Активные кредиты ({credits.filter(c => ['active','overdue'].includes(c.status)).length})
                </h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {credits.filter(c => ['active','overdue'].includes(c.status)).map(c => (
                    <div key={c.id} className={`p-4 bg-white/5 rounded-lg text-sm border ${c.status === 'overdue' ? 'border-red-500/30 bg-red-500/5' : 'border-white/10'}`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-1 rounded font-bold ${c.status === 'overdue' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
                            {c.status === 'overdue' ? '⚠️ ПРОСРОЧЕН' : '✓ Активный'}
                          </span>
                          <span className="text-text-muted">{c.lender_name}</span>
                        </div>
                        {c.status === 'overdue' && c.seized_building && (
                          <span className="text-xs px-2 py-1 bg-purple-500/20 text-purple-400 rounded">
                            🏢 Здание изъято
                          </span>
                        )}
                      </div>
                      
                      {/* Full borrower ID with copy */}
                      <div className="mb-3 flex items-center gap-2">
                        <span className="text-text-muted text-xs">ID заёмщика:</span>
                        <code 
                          className="text-white font-mono text-xs bg-white/10 px-2 py-1 rounded cursor-pointer hover:bg-white/20 transition-colors"
                          onClick={() => {
                            navigator.clipboard.writeText(c.borrower_id);
                            toast.success('ID скопирован!');
                          }}
                          title="Нажмите для копирования"
                        >
                          {c.borrower_id}
                        </code>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                        <div className="bg-white/5 p-2 rounded">
                          <span className="text-text-muted block">Сумма</span>
                          <span className="text-white font-bold">{c.amount} TON</span>
                        </div>
                        <div className="bg-white/5 p-2 rounded">
                          <span className="text-text-muted block">Ставка</span>
                          <span className="text-white font-bold">{(c.interest_rate*100).toFixed(0)}%</span>
                        </div>
                        <div className="bg-white/5 p-2 rounded">
                          <span className="text-text-muted block">Остаток</span>
                          <span className="text-amber-400 font-bold">{c.remaining?.toFixed(2)} TON</span>
                        </div>
                        <div className="bg-white/5 p-2 rounded">
                          <span className="text-text-muted block">Удержание</span>
                          <span className="text-white font-bold">{(c.salary_deduction_percent*100).toFixed(0)}%</span>
                        </div>
                      </div>
                      
                      {/* Seized building info */}
                      {c.status === 'overdue' && c.seized_building && (
                        <div className="mt-3 p-2 bg-purple-500/10 border border-purple-500/20 rounded text-xs">
                          <span className="text-purple-400">Изъятое здание: </span>
                          <span className="text-white">{c.seized_building.type} (Level {c.seized_building.level})</span>
                          <span className="text-text-muted ml-2">→ Выставлено на торги</span>
                        </div>
                      )}
                    </div>
                  ))}
                  {credits.filter(c => ['active','overdue'].includes(c.status)).length === 0 && (
                    <p className="text-text-muted text-center py-8">Нет активных кредитов</p>
                  )}
                </div>
              </div>
              
              {/* History of paid credits */}
              <div className="glass-panel rounded-xl p-4 border border-green-500/20">
                <h3 className="font-unbounded text-sm font-bold text-white mb-3">
                  Погашенные кредиты ({credits.filter(c => c.status === 'paid').length})
                </h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {credits.filter(c => c.status === 'paid').map(c => (
                    <div key={c.id} className="p-2 bg-green-500/5 rounded-lg text-xs border border-green-500/20">
                      <div className="flex justify-between items-center">
                        <code 
                          className="text-white font-mono cursor-pointer hover:text-green-400"
                          onClick={() => {
                            navigator.clipboard.writeText(c.borrower_id);
                            toast.success('ID скопирован!');
                          }}
                        >
                          {c.borrower_id}
                        </code>
                        <span className="text-green-400">✓ {c.amount} TON погашено</span>
                      </div>
                    </div>
                  ))}
                  {credits.filter(c => c.status === 'paid').length === 0 && (
                    <p className="text-text-muted text-center py-4">Нет погашенных кредитов</p>
                  )}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* USER DETAILS TAB */}
          <TabsContent value="userdetails">
            <div className="space-y-4">
              <div className="glass-panel rounded-xl p-4 border border-purple-500/20">
                <h3 className="font-unbounded text-sm font-bold text-white mb-3">Поиск пользователя</h3>
                <div className="flex gap-3">
                  <Input
                    data-testid="user-search-input"
                    placeholder="ID, email или wallet"
                    value={userDetailId}
                    onChange={(e) => setUserDetailId(e.target.value)}
                    className="bg-white/5 border-white/10"
                    onKeyDown={(e) => e.key === 'Enter' && handleLoadUserDetail()}
                  />
                  <Button onClick={handleLoadUserDetail} disabled={loadingDetail} className="btn-cyber">
                    {loadingDetail ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Найти'}
                  </Button>
                </div>
              </div>

              {userDetail && (
                <div className="glass-panel rounded-xl p-4 border border-white/10 space-y-4">
                  <div className="flex items-center gap-3 pb-3 border-b border-white/10">
                    <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 font-bold">
                      {(userDetail.user?.username || '?')[0]}
                    </div>
                    <div>
                      <div className="text-white font-bold">{userDetail.user?.username || 'N/A'}</div>
                      <div className="text-text-muted text-xs">{userDetail.user?.email || userDetail.user?.wallet_address?.slice(0,12)+'...'}</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="p-3 bg-green-500/10 rounded-lg">
                      <div className="text-xs text-text-muted">Баланс</div>
                      <div className="text-lg font-bold text-green-400">{userDetail.balance?.toFixed(2)} TON</div>
                    </div>
                    <div className="p-3 bg-amber-500/10 rounded-lg">
                      <div className="text-xs text-text-muted">Долг</div>
                      <div className="text-lg font-bold text-amber-400">{userDetail.active_debt?.toFixed(2)} TON</div>
                    </div>
                    <div className="p-3 bg-cyan-500/10 rounded-lg">
                      <div className="text-xs text-text-muted">Стоимость бизнесов</div>
                      <div className="text-lg font-bold text-cyan-400">{userDetail.total_business_value?.toFixed(2)} TON</div>
                    </div>
                    <div className="p-3 bg-purple-500/10 rounded-lg">
                      <div className="text-xs text-text-muted">Доступный вывод</div>
                      <div className="text-lg font-bold text-purple-400">{userDetail.available_withdrawal?.toFixed(2)} TON</div>
                    </div>
                  </div>

                  {/* Businesses */}
                  {userDetail.businesses?.length > 0 && (
                    <div>
                      <h4 className="text-white font-bold text-sm mb-2">Бизнесы ({userDetail.businesses_count})</h4>
                      <div className="space-y-1">
                        {userDetail.businesses.map(b => (
                          <div key={b.id} className="flex items-center justify-between p-2 bg-white/5 rounded text-sm">
                            <span className="text-white">{b.type}</span>
                            <span className="text-text-muted">Ур. {b.level}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Credits */}
                  {userDetail.credits?.length > 0 && (
                    <div>
                      <h4 className="text-white font-bold text-sm mb-2">Кредиты</h4>
                      <div className="space-y-1">
                        {userDetail.credits.map(c => (
                          <div key={c.id} className={`p-2 rounded text-sm border ${c.status === 'overdue' ? 'bg-red-500/10 border-red-500/20' : c.status === 'active' ? 'bg-amber-500/10 border-amber-500/20' : 'bg-white/5 border-white/10'}`}>
                            <div className="flex items-center justify-between">
                              <span className="text-white">{c.amount} TON ({c.lender_name})</span>
                              <span className={c.status === 'overdue' ? 'text-red-400' : c.status === 'active' ? 'text-amber-400' : 'text-green-400'}>
                                {c.status === 'overdue' ? 'Просрочен' : c.status === 'active' ? 'Активный' : 'Погашен'} | Остаток: {c.remaining?.toFixed(2)}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Tax Settings Tab */}
          <TabsContent value="taxes">
            <div className="glass-panel rounded-2xl p-6">
              <h2 className="font-unbounded text-lg font-bold text-text-main mb-6">
                Налоговые настройки
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm text-text-muted">Налог на продажу мелких бизнесов (Tier 1) %</label>
                  <Input 
                    type="number"
                    value={taxSettings.small_business_tax || 5}
                    onChange={(e) => setTaxSettings({...taxSettings, small_business_tax: parseFloat(e.target.value) || 0})}
                    className="bg-white/5 border-white/10"
                  />
                  <p className="text-xs text-text-muted">Применяется к бизнесам Tier 1</p>
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-text-muted">Налог на продажу средних бизнесов (Tier 2) %</label>
                  <Input 
                    type="number"
                    value={taxSettings.medium_business_tax || 8}
                    onChange={(e) => setTaxSettings({...taxSettings, medium_business_tax: parseFloat(e.target.value) || 0})}
                    className="bg-white/5 border-white/10"
                  />
                  <p className="text-xs text-text-muted">Применяется к бизнесам Tier 2</p>
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-text-muted">Налог на продажу крупных бизнесов (Tier 3) %</label>
                  <Input 
                    type="number"
                    value={taxSettings.large_business_tax || 10}
                    onChange={(e) => setTaxSettings({...taxSettings, large_business_tax: parseFloat(e.target.value) || 0})}
                    className="bg-white/5 border-white/10"
                  />
                  <p className="text-xs text-text-muted">Применяется к бизнесам Tier 3</p>
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-text-muted">Налог на продажу земли с бизнесом %</label>
                  <Input 
                    type="number"
                    value={taxSettings.land_business_sale_tax || 10}
                    onChange={(e) => setTaxSettings({...taxSettings, land_business_sale_tax: parseFloat(e.target.value) || 0})}
                    className="bg-white/5 border-white/10"
                  />
                  <p className="text-xs text-text-muted">Применяется при продаже участка с бизнесом на маркетплейсе</p>
                </div>
              </div>
              
              <Button 
                onClick={saveTaxSettings}
                className="mt-6 bg-cyber-cyan text-black hover:bg-cyber-cyan/80"
              >
                Сохранить налоги
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
