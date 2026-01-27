import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTonWallet } from '@tonconnect/ui-react';
import { motion } from 'framer-motion';
import { 
  Users, Building2, DollarSign, TrendingUp, Settings, 
  CreditCard, Bell, Gift, RefreshCw, Check, X, ArrowLeft, Wallet, Copy
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useTranslation } from '@/lib/translations';
import { toast } from 'sonner';
import axios from 'axios';
import WalletSettings from '@/components/WalletSettings';
import RevenueAnalytics from '@/components/RevenueAnalytics';
import TreasuryWarning from '@/components/TreasuryWarning';
import { toUserFriendlyAddress } from '@/lib/tonAddress';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminPage() {
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
  
  // Form states
  const [promoName, setPromoName] = useState('');
  const [promoAmount, setPromoAmount] = useState('');
  const [promoMaxUses, setPromoMaxUses] = useState('');
  const [announcementTitle, setAnnouncementTitle] = useState('');
  const [announcementMessage, setAnnouncementMessage] = useState('');

  const token = localStorage.getItem('ton_city_token');

  useEffect(() => {
    if (!wallet?.account || !token) {
      navigate('/');
      return;
    }
    checkAdmin();
  }, [wallet, token]);

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
    } catch (error) {
      console.error('Admin check failed:', error);
      navigate('/');
    }
  };

  const loadData = async () => {
    setIsLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      const [statsRes, usersRes, txRes, promosRes, announcementsRes, treasuryRes] = await Promise.all([
        axios.get(`${API}/admin/stats`, { headers }),
        axios.get(`${API}/admin/users?limit=50`, { headers }),
        axios.get(`${API}/admin/transactions?limit=100`, { headers }),
        axios.get(`${API}/admin/promos`, { headers }).catch(() => ({ data: { promos: [] } })),
        axios.get(`${API}/admin/announcements`, { headers }).catch(() => ({ data: { announcements: [] } })),
        axios.get(`${API}/admin/treasury-health`, { headers }).catch(() => ({ data: {} })),
      ]);
      
      setStats(statsRes.data);
      setUsers(usersRes.data.users || []);
      setTransactions(txRes.data.transactions || []);
      setPromos(promosRes.data.promos || []);
      setAnnouncements(announcementsRes.data.announcements || []);
      setTreasuryHealth(treasuryRes.data);
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
      loadData();
    } catch (error) {
<<<<<<< HEAD
      const msg = error.response?.data?.detail || 'Failed to approve';
      toast.error(msg);
=======
      toast.error('Failed to approve');
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
    }
  };

  const rejectWithdrawal = async (txId) => {
    try {
      await axios.post(`${API}/admin/withdrawal/reject/${txId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Withdrawal rejected and refunded');
      loadData();
    } catch (error) {
      toast.error('Failed to reject');
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

<<<<<<< HEAD
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
=======
  // Show full address with copy button - in user-friendly format
  const AddressDisplay = ({ address, short = false }) => {
    if (!address) return <span className="text-text-muted">-</span>;
    
    // Convert raw address (0:...) to user-friendly format (UQ.../EQ...)
    const friendlyAddress = toUserFriendlyAddress(address);
    
    const copyToClipboard = () => {
      navigator.clipboard.writeText(friendlyAddress);
      toast.success('Адрес скопирован');
    };
    
    const displayAddress = short 
      ? `${friendlyAddress.slice(0, 8)}...${friendlyAddress.slice(-6)}` 
      : friendlyAddress;
    
    return (
      <div className="flex items-center gap-2 group">
        <span className="font-mono text-sm break-all" title={friendlyAddress}>
          {displayAddress}
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
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
      <header className="glass-panel border-b border-grid-border px-6 py-4">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/game')}
              className="text-text-muted hover:text-text-main"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('back')}
            </Button>
            <h1 className="font-unbounded text-xl font-bold text-text-main flex items-center gap-2">
              <Settings className="w-5 h-5 text-cyber-cyan" />
              {t('adminPanel')}
            </h1>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            className="border-grid-border"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            {t('refresh')}
          </Button>
        </div>
      </header>

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
              <h2 className="font-unbounded text-lg font-bold text-text-main mb-6">
                {t('pendingWithdrawals')}
              </h2>
              
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
                        className="glass-panel rounded-lg p-4"
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex-1 space-y-2">
                            <div>
<<<<<<< HEAD
                              <div className="text-xs text-text-muted mb-1">Куда (To):</div>
                              <AddressDisplay address={tx.to_address_display || tx.to_address} />
=======
                              <div className="text-xs text-text-muted mb-1">От кого (From):</div>
                              <AddressDisplay address={tx.from_address} />
                            </div>
                            <div>
                              <div className="text-xs text-text-muted mb-1">Куда (To):</div>
                              <AddressDisplay address={tx.to_address} />
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
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
                          Balance: {(user.balance_game || 0).toFixed(2)} TON
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
            <div className="glass-panel rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-unbounded text-lg font-bold text-text-main">
                  Promo Codes
                </h2>
                
                <Dialog>
                  <DialogTrigger asChild>
                    <Button className="btn-cyber">
                      <Gift className="w-4 h-4 mr-2" />
                      {t('createPromo')}
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="glass-panel border-grid-border text-text-main">
                    <DialogHeader>
                      <DialogTitle>Create Promo Code</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <Input
                        placeholder="Promo name"
                        value={promoName}
                        onChange={(e) => setPromoName(e.target.value)}
                        className="bg-panel border-grid-border"
                      />
                      <Input
                        type="number"
                        placeholder="Amount (TON)"
                        value={promoAmount}
                        onChange={(e) => setPromoAmount(e.target.value)}
                        className="bg-panel border-grid-border"
                      />
                      <Input
                        type="number"
                        placeholder="Max uses"
                        value={promoMaxUses}
                        onChange={(e) => setPromoMaxUses(e.target.value)}
                        className="bg-panel border-grid-border"
                      />
                      <Button onClick={createPromo} className="w-full btn-cyber">
                        Create
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
              
              <div className="space-y-3">
                {promos.map((promo) => (
                  <div
                    key={promo.id}
                    className="glass-panel rounded-lg p-4 flex items-center gap-4"
                  >
                    <div className="flex-1">
                      <div className="font-mono text-lg text-cyber-cyan">
                        {promo.code}
                      </div>
                      <div className="text-sm text-text-muted">
                        {promo.name}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-signal-amber">
                        {promo.amount} TON
                      </div>
                      <div className="text-xs text-text-muted">
                        Used: {promo.current_uses}/{promo.max_uses}
                      </div>
                    </div>
                  </div>
                ))}
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
        </Tabs>
      </main>
    </div>
  );
}
