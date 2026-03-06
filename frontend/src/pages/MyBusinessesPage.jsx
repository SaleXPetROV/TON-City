import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Building2, Package, Coins, TrendingUp, RefreshCw, 
  Settings2, Wrench, Zap, ArrowUp, ChevronRight,
  Play, Pause, Check, X, AlertCircle, Shield, Heart,
  Crown, Users, Warehouse, Clock, Loader2, Tag
} from 'lucide-react';
import PageHeader from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import Sidebar from '@/components/Sidebar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Tier colors
const TIER_COLORS = {
  1: 'bg-green-500/20 text-green-400 border-green-500/30',
  2: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  3: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
};

// Resource icons - V2.0
const resourceIcons = {
  energy: '⚡',
  cu: '🖥️',
  quartz: '💎',
  traffic: '📡',
  cooling: '❄️',
  biomass: '🌿',
  scrap: '🗑️',
  chips: '🔲',
  nft: '🎨',
  neurocode: '🧠',
  logistics: '🚚',
  repair_kits: '🔧',
  vr_experience: '🥽',
  profit_ton: '💰',
  shares: '📈',
  ton: '💎',
  // Backward compat
  food: '🌿',
  algo: '🧠',
  iron: '🔧',
};

export default function MyBusinessesPage({ user, refreshBalance, updateBalance }) {
  const navigate = useNavigate();
  const [businesses, setBusinesses] = useState([]);
  const [summary, setSummary] = useState({});
  const [resourcesFromBusinesses, setResourcesFromBusinesses] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [patrons, setPatrons] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  
  // Modals
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showRepairModal, setShowRepairModal] = useState(false);
  const [showPatronModal, setShowPatronModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showSellModal, setShowSellModal] = useState(false);
  const [sellPrice, setSellPrice] = useState('');
  const [sellTaxInfo, setSellTaxInfo] = useState(null);
  
  // Loading states
  const [isCollecting, setIsCollecting] = useState(false);
  const [isUpgrading, setIsUpgrading] = useState(false);
  const [isRepairing, setIsRepairing] = useState(false);
  const [isSelling, setIsSelling] = useState(false);
  
  const token = localStorage.getItem('token');

  // Форматирование адреса кошелька
  const formatWalletAddress = (address) => {
    if (!address) return 'Не привязан';
    if (address.length <= 15) return address;
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  // Расчет налога при продаже
  const calculateSaleTax = async (price) => {
    try {
      const res = await fetch(`${API}/business/calculate-sale-tax`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price: parseFloat(price) })
      });
      if (res.ok) {
        const data = await res.json();
        setSellTaxInfo(data);
      }
    } catch (error) {
      console.error('Failed to calculate tax:', error);
    }
  };

  // Продажа бизнеса
  const handleSellBusiness = async () => {
    if (!selectedBusiness || !sellPrice) return;
    
    setIsSelling(true);
    try {
      const res = await fetch(`${API}/business/${selectedBusiness.id}/sell`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          business_id: selectedBusiness.id,
          price: parseFloat(sellPrice)
        })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to list business');
      }
      
      const data = await res.json();
      toast.success(`Бизнес выставлен на продажу! Вы получите ${data.listing.seller_receives} TON`);
      setShowSellModal(false);
      setSellPrice('');
      setSellTaxInfo(null);
      fetchData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsSelling(false);
    }
  };

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [bizRes, patronsRes, resourcesRes] = await Promise.all([
        fetch(`${API}/my/businesses`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
        fetch(`${API}/patrons`).then(r => r.json()),
        fetch(`${API}/my/resources`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).catch(() => ({ resources: {} }))
      ]);
      
      setBusinesses(bizRes.businesses || []);
      setSummary(bizRes.summary || {});
      setPatrons(patronsRes.patrons || []);
      setResourcesFromBusinesses(resourcesRes.resources || {});
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch businesses:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!token) {
      navigate('/auth?mode=login');
      return;
    }
    fetchData();
    
    // Silent refresh every 60 seconds (no loading spinner)
    const interval = setInterval(() => {
      // Fetch without setting isLoading to true
      Promise.all([
        fetch(`${API}/my/businesses`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
        fetch(`${API}/my/resources`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).catch(() => ({ resources: {} }))
      ]).then(([bizRes, resourcesRes]) => {
        setBusinesses(bizRes.businesses || []);
        setSummary(bizRes.summary || {});
        setResourcesFromBusinesses(resourcesRes.resources || {});
        setLastUpdate(new Date());
      }).catch(() => {});
    }, 60000); // 1 minute
    return () => clearInterval(interval);
  }, [user]);

  // Collect all income
  const handleCollectAll = async () => {
    setIsCollecting(true);
    try {
      const res = await fetch(`${API}/my/collect-all`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error('Ошибка сбора');
      
      const data = await res.json();
      
      // Мгновенное отображение начисления
      toast.success(
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-2xl animate-bounce">💰</span>
            <span className="text-lg font-bold text-green-400">+{data.total_player_income.toFixed(2)} TON</span>
          </div>
          <div className="text-xs text-gray-400">Собрано с {data.businesses_collected} бизнесов</div>
          <div className="text-xs text-amber-400">Налог: -{data.total_tax_paid.toFixed(2)} TON</div>
        </div>,
        { duration: 5000 }
      );
      
      // Update global balance
      if (refreshBalance) refreshBalance();
      if (updateBalance && data.new_balance !== undefined) {
        updateBalance(data.new_balance);
      }
      
      setLastUpdate(new Date());
      fetchData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsCollecting(false);
    }
  };

  // Collect single business
  const handleCollect = async (businessId) => {
    try {
      const res = await fetch(`${API}/business/${businessId}/collect`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка сбора');
      }
      
      const data = await res.json();
      
      // Мгновенное визуальное начисление
      toast.success(
        <div className="flex items-center gap-2">
          <span className="text-xl animate-bounce">💰</span>
          <span className="font-bold text-green-400">+{data.player_receives.toFixed(2)} TON</span>
        </div>,
        { duration: 3000 }
      );
      
      fetchData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  // Upgrade business
  const handleUpgrade = async () => {
    if (!selectedBusiness) return;
    setIsUpgrading(true);
    
    try {
      const res = await fetch(`${API}/business/${selectedBusiness.id}/upgrade`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка улучшения');
      }
      
      const data = await res.json();
      toast.success(`Улучшено до уровня ${data.new_level}!`);
      setShowUpgradeModal(false);
      fetchData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsUpgrading(false);
    }
  };

  // Repair business
  const handleRepair = async () => {
    if (!selectedBusiness) return;
    setIsRepairing(true);
    
    try {
      const res = await fetch(`${API}/business/${selectedBusiness.id}/repair`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка ремонта');
      }
      
      const data = await res.json();
      toast.success(`Отремонтировано! Оплачено: ${data.cost_paid.toFixed(2)} TON`);
      setShowRepairModal(false);
      fetchData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsRepairing(false);
    }
  };

  // Set patron
  const handleSetPatron = async (patronId) => {
    if (!selectedBusiness) return;
    
    try {
      const url = patronId 
        ? `${API}/business/${selectedBusiness.id}/set-patron?patron_id=${patronId}`
        : `${API}/business/${selectedBusiness.id}/set-patron`;
        
      const res = await fetch(url, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка назначения патрона');
      }
      
      toast.success(patronId ? 'Патрон назначен!' : 'Патрон удалён');
      setShowPatronModal(false);
      fetchData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  // Open business details
  const openDetails = async (biz) => {
    try {
      const res = await fetch(`${API}/business/${biz.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setSelectedBusiness({ ...biz, ...data });
      setShowDetailsModal(true);
    } catch (error) {
      setSelectedBusiness(biz);
      setShowDetailsModal(true);
    }
  };

  // Get durability color
  const getDurabilityColor = (durability) => {
    if (durability >= 70) return 'bg-green-500';
    if (durability >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (isLoading) {
    return (
      <div className="flex h-screen bg-void">
        <Sidebar user={user} />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-12 h-12 text-cyber-cyan animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-void">
      <Sidebar user={user} />
      
      <div className="flex-1 overflow-hidden lg:ml-16">
        <ScrollArea className="h-full">
          <div className="p-4 lg:p-6 pt-4 lg:pt-6 space-y-4 lg:space-y-6">
            {/* Header - Mobile Optimized */}
            <PageHeader 
              icon={<Building2 className="w-6 h-6 lg:w-8 lg:h-8 text-cyber-cyan" />}
              title="МОИ БИЗНЕСЫ"
              rightContent={
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-text-muted hidden md:inline">
                    Обновлено: {lastUpdate.toLocaleTimeString('ru-RU')}
                  </span>
                  <Button onClick={fetchData} variant="outline" size="sm" className="border-white/10" disabled={isLoading}>
                    <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
              }
            />
            <p className="text-text-muted text-sm -mt-2">Управление и апгрейды • Автообновление каждые 30 сек</p>
              
            {businesses.length > 0 && summary.total_pending_income > 0 && (
              <Button 
                onClick={handleCollectAll} 
                size="sm"
                className="bg-green-600 hover:bg-green-700"
                disabled={isCollecting}
              >
                {isCollecting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Coins className="w-4 h-4" />
                )}
                <span className="ml-2">{summary.total_pending_income?.toFixed(1)} TON</span>
              </Button>
            )}

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="glass-panel border-white/10">
                <CardContent className="p-4 flex items-center gap-3">
                  <Building2 className="w-8 h-8 text-cyber-cyan" />
                  <div>
                    <div className="text-2xl font-bold text-white">{summary.total_businesses || 0}</div>
                    <div className="text-xs text-text-muted">Всего бизнесов</div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="glass-panel border-green-500/20">
                <CardContent className="p-4 flex items-center gap-3">
                  <Coins className="w-8 h-8 text-green-400" />
                  <div>
                    <div className="text-2xl font-bold text-green-400">
                      {summary.total_pending_income?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-xs text-text-muted">Доход (TON)</div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="glass-panel border-yellow-500/20">
                <CardContent className="p-4 flex items-center gap-3">
                  <TrendingUp className="w-8 h-8 text-yellow-400" />
                  <div>
                    <div className="text-2xl font-bold text-yellow-400">
                      {summary.total_daily_income?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-xs text-text-muted">В день (TON)</div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="glass-panel border-purple-500/20">
                <CardContent className="p-4 flex items-center gap-3">
                  <Package className="w-8 h-8 text-purple-400" />
                  <div>
                    <div className="text-2xl font-bold text-purple-400">
                      {summary.total_warehouse_used || 0}/{summary.total_warehouse_capacity || 0}
                    </div>
                    <div className="text-xs text-text-muted">Общий склад</div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Businesses List */}
            {businesses.length === 0 ? (
              <Card className="glass-panel border-white/10">
                <CardContent className="p-12 text-center">
                  <Building2 className="w-16 h-16 text-text-muted mx-auto mb-4" />
                  <h3 className="text-xl font-bold text-white mb-2">У вас пока нет бизнесов</h3>
                  <p className="text-text-muted mb-4">
                    Купите участок и постройте свой первый бизнес на острове TON
                  </p>
                  <Button onClick={() => navigate('/island')} className="bg-cyber-cyan text-black">
                    Перейти на остров
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {businesses.map((biz) => (
                  <motion.div
                    key={biz.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="group"
                  >
                    <Card className="glass-panel border-white/10 hover:border-cyber-cyan/30 transition-all">
                      <CardContent className="p-4">
                        {/* Header */}
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="text-3xl">{biz.config?.icon || '🏢'}</div>
                            <div>
                              <h3 className="font-bold text-white">
                                {biz.config?.name?.ru || biz.config?.name?.en || biz.business_type}
                              </h3>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge className={TIER_COLORS[biz.config?.tier || 1]}>
                                  Tier {biz.config?.tier || 1}
                                </Badge>
                                <Badge variant="outline" className="border-white/20">
                                  Ур. {biz.level || 1}
                                </Badge>
                              </div>
                            </div>
                          </div>
                          
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => openDetails(biz)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Settings2 className="w-4 h-4" />
                          </Button>
                        </div>
                        
                        {/* Durability Bar */}
                        <div className="mb-3">
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-text-muted flex items-center gap-1">
                              <Heart className="w-3 h-3" /> Прочность
                            </span>
                            <span className={biz.durability < 30 ? 'text-red-400' : 'text-white'}>
                              {biz.durability?.toFixed(1) || 100}%
                            </span>
                          </div>
                          <Progress 
                            value={biz.durability || 100} 
                            className="h-2" 
                          />
                          {biz.durability < 30 && (
                            <div className="flex items-center gap-1 text-red-400 text-xs mt-1">
                              <AlertCircle className="w-3 h-3" />
                              Требуется ремонт!
                            </div>
                          )}
                        </div>
                        
                        {/* Production & Storage Status */}
                        <div className="p-3 bg-white/5 rounded-lg mb-3">
                          {/* Work status badge with reason */}
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-text-muted">Статус:</span>
                            {(() => {
                              // Determine work status and reason
                              let status = 'working';
                              let reason = '';
                              
                              // Check if on sale first
                              if (biz.on_sale) {
                                status = 'on_sale';
                                reason = 'Выставлен на продажу';
                              } else if (biz.durability <= 0) {
                                status = 'stopped';
                                reason = '0% прочности';
                              } else if (biz.storage_info?.is_full) {
                                status = 'stopped';
                                reason = 'Склад полон';
                              } else if (biz.work_status === 'idle') {
                                status = 'idle';
                                reason = 'Нет ресурсов';
                              } else if (biz.work_status === 'stopped') {
                                status = 'stopped';
                                reason = biz.stop_reason || 'Остановлен';
                              }
                              
                              return (
                                <div className="flex flex-col items-end">
                                  <Badge data-testid={`work-status-${biz.id}`} className={
                                    status === 'working' 
                                      ? 'bg-green-500/20 text-green-400' 
                                      : status === 'on_sale'
                                      ? 'bg-amber-500/20 text-amber-400'
                                      : status === 'idle'
                                      ? 'bg-yellow-500/20 text-yellow-400'
                                      : 'bg-red-500/20 text-red-400'
                                  }>
                                    {status === 'working' ? 'Работает' : 
                                     status === 'on_sale' ? 'На продаже' :
                                     status === 'idle' ? 'Простаивает' : 'Остановлен'}
                                  </Badge>
                                  {reason && (
                                    <span className={`text-xs mt-0.5 ${status === 'on_sale' ? 'text-amber-400' : 'text-red-400'}`}>{reason}</span>
                                  )}
                                </div>
                              );
                            })()}
                          </div>
                          
                          {/* Production info - what it produces */}
                          {biz.config?.produces && (
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-text-muted">Производит:</span>
                              <span className="text-cyan-300 font-medium flex items-center gap-1">
                                {resourceIcons[biz.config.produces] || '📦'} {biz.config.produces}
                              </span>
                            </div>
                          )}
                          
                          {/* Production amount based on durability */}
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-text-muted">Выход/час:</span>
                            <span className="text-green-400 font-mono">
                              {Math.round((biz.production?.base_production || biz.config?.base_production || 100) * (biz.durability || 100) / 100)} ед.
                            </span>
                          </div>
                          
                          {/* Storage bar */}
                          {biz.storage_info && biz.storage_info.capacity > 0 && (
                            <div className="mt-2">
                              <div className="flex justify-between text-xs mb-1">
                                <span className="text-text-muted flex items-center gap-1">
                                  <Package className="w-3 h-3" /> Склад
                                </span>
                                <span className={biz.storage_info.is_full ? 'text-red-400 font-bold' : 'text-white'}>
                                  {biz.storage_info.used}/{biz.storage_info.capacity}
                                </span>
                              </div>
                              <div className="w-full bg-gray-700 rounded-full h-2">
                                <div 
                                  className={`h-2 rounded-full transition-all ${
                                    biz.storage_info.is_full ? 'bg-red-500' : 
                                    biz.storage_info.used / biz.storage_info.capacity > 0.8 ? 'bg-yellow-500' : 'bg-cyan-500'
                                  }`}
                                  style={{ width: `${Math.min(100, (biz.storage_info.used / biz.storage_info.capacity) * 100)}%` }}
                                />
                              </div>
                              {biz.storage_info.is_full && (
                                <div className="text-red-400 text-xs mt-1 flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3" />
                                  Склад полон — продайте ресурсы в Торговле!
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                        
                        {/* Patron Badge */}
                        {biz.patron && (
                          <div className="flex items-center gap-2 p-2 bg-purple-500/10 rounded-lg mb-3">
                            <Crown className="w-4 h-4 text-purple-400" />
                            <span className="text-xs text-purple-300">
                              Патрон: {biz.patron.type} (Ур. {biz.patron.level})
                            </span>
                          </div>
                        )}
                        
                        {/* Actions - NO COLLECT BUTTON, businesses produce resources not TON */}
                        <div className="flex gap-2 mt-3">
                          {biz.level < 10 && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="flex-1 border-blue-500/30 text-blue-400"
                              onClick={() => {
                                setSelectedBusiness(biz);
                                setShowUpgradeModal(true);
                              }}
                            >
                              <ArrowUp className="w-4 h-4 mr-1" />
                              Улучшить
                            </Button>
                          )}
                          
                          {biz.durability < 100 && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="flex-1 border-yellow-500/30 text-yellow-400"
                              onClick={() => {
                                setSelectedBusiness(biz);
                                setShowRepairModal(true);
                              }}
                            >
                              <Wrench className="w-4 h-4 mr-1" />
                              Ремонт
                            </Button>
                          )}
                          
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-purple-500/30 text-purple-400"
                            onClick={() => {
                              setSelectedBusiness(biz);
                              setShowPatronModal(true);
                            }}
                          >
                            <Crown className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}

            {/* Storage/Resources Section */}
            <div className="mt-8">
              <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                <Package className="w-5 h-5 text-amber-400" />
                Мои ресурсы
              </h2>
              
              <Card className="glass-panel border-amber-500/20">
                <CardContent className="p-4">
                  {Object.keys(resourcesFromBusinesses).length === 0 ? (
                    <div className="text-center py-6 text-text-muted">
                      <Package className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>Нет накопленных ресурсов</p>
                      <p className="text-xs mt-1">Бизнесы производят ресурсы автоматически</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                      {Object.entries(resourcesFromBusinesses).map(([resource, amount]) => (
                        <div 
                          key={resource}
                          className="bg-white/5 rounded-lg p-3 text-center border border-white/10 hover:border-amber-500/30 transition-colors"
                        >
                          <div className="text-2xl mb-1">
                            {resourceIcons[resource] || '📦'}
                          </div>
                          <div className="text-lg font-bold text-white">{Math.floor(amount)}</div>
                          <div className="text-xs text-text-muted capitalize">{resource}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </ScrollArea>
      </div>

      {/* Upgrade Modal */}
      <Dialog open={showUpgradeModal} onOpenChange={setShowUpgradeModal}>
        <DialogContent className="bg-void border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <ArrowUp className="w-5 h-5 text-blue-400" />
              Улучшение бизнеса
            </DialogTitle>
          </DialogHeader>
          
          {selectedBusiness && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-4 bg-white/5 rounded-xl">
                <span className="text-3xl">{selectedBusiness.config?.icon}</span>
                <div>
                  <div className="text-white font-bold">
                    {selectedBusiness.config?.name?.ru}
                  </div>
                  <div className="text-text-muted text-sm">
                    Уровень {selectedBusiness.level} → {selectedBusiness.level + 1}
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-text-muted">Доход после улучшения:</span>
                  <span className="text-green-400">+20%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-text-muted">Новая ёмкость склада:</span>
                  <span className="text-white">+{Math.floor(selectedBusiness.storage?.capacity * 0.2 || 10)}</span>
                </div>
              </div>
              
              <div className="p-3 bg-blue-500/10 rounded-lg">
                <div className="text-xs text-text-muted mb-1">Стоимость улучшения:</div>
                <div className="text-xl font-bold text-blue-400">
                  {((selectedBusiness.config?.base_cost_ton || selectedBusiness.config?.cost || 5) * Math.pow(1.8, selectedBusiness.level || 1)).toFixed(2)} TON
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUpgradeModal(false)} className="border-white/10">
              Отмена
            </Button>
            <Button 
              onClick={handleUpgrade} 
              className="bg-blue-600"
              disabled={isUpgrading}
            >
              {isUpgrading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Улучшить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Repair Modal */}
      <Dialog open={showRepairModal} onOpenChange={setShowRepairModal}>
        <DialogContent className="bg-void border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Wrench className="w-5 h-5 text-yellow-400" />
              Ремонт бизнеса
            </DialogTitle>
          </DialogHeader>
          
          {selectedBusiness && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-4 bg-white/5 rounded-xl">
                <span className="text-3xl">{selectedBusiness.config?.icon}</span>
                <div>
                  <div className="text-white font-bold">
                    {selectedBusiness.config?.name?.ru}
                  </div>
                  <div className="text-red-400 text-sm">
                    Прочность: {selectedBusiness.durability?.toFixed(1)}%
                  </div>
                </div>
              </div>
              
              <div className="p-3 bg-yellow-500/10 rounded-lg">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-text-muted">Текущая прочность:</span>
                  <span className="text-yellow-400">{selectedBusiness.durability?.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-text-muted">После ремонта:</span>
                  <span className="text-green-400">100%</span>
                </div>
              </div>
              
              <div className="p-3 bg-white/5 rounded-lg">
                <div className="text-xs text-text-muted mb-1">Стоимость ремонта:</div>
                <div className="text-xl font-bold text-yellow-400">
                  ~{((100 - (selectedBusiness.durability || 0)) * 0.001).toFixed(2)} TON
                </div>
              </div>
              
              <p className="text-xs text-text-muted">
                При прочности 0% производство полностью останавливается. 
                Регулярный ремонт экономит деньги.
              </p>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRepairModal(false)} className="border-white/10">
              Отмена
            </Button>
            <Button 
              onClick={handleRepair} 
              className="bg-yellow-600"
              disabled={isRepairing}
            >
              {isRepairing ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Отремонтировать
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Patron Modal */}
      <Dialog open={showPatronModal} onOpenChange={setShowPatronModal}>
        <DialogContent className="bg-void border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Crown className="w-5 h-5 text-purple-400" />
              Выбор патрона
            </DialogTitle>
            <DialogDescription className="text-text-muted">
              Патрон получает 1% от вашего дохода, но даёт бонусы к производству
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {/* Remove patron option */}
            {selectedBusiness?.patron && (
              <Button
                variant="outline"
                className="w-full justify-start border-red-500/30 text-red-400"
                onClick={() => handleSetPatron(null)}
              >
                <X className="w-4 h-4 mr-2" />
                Убрать патрона
              </Button>
            )}
            
            {patrons.length === 0 ? (
              <div className="text-center py-8 text-text-muted">
                <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Патроны пока недоступны</p>
              </div>
            ) : (
              patrons.map(patron => (
                <div
                  key={patron.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedBusiness?.patron?.id === patron.id
                      ? 'border-purple-500 bg-purple-500/10'
                      : 'border-white/10 hover:border-white/30 bg-white/5'
                  }`}
                  onClick={() => handleSetPatron(patron.id)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{patron.icon}</span>
                    <div className="flex-1">
                      <div className="text-white font-medium">
                        {patron.name?.ru || patron.type}
                      </div>
                      <div className="text-xs text-text-muted">
                        Владелец: {patron.owner_name} • Ур. {patron.level}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-purple-400 text-sm">
                        +{((patron.current_bonus - 1) * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-text-muted">
                        {patron.bonus_type}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPatronModal(false)} className="border-white/10">
              Закрыть
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Details Modal */}
      <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
        <DialogContent className="bg-void border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Settings2 className="w-5 h-5 text-cyber-cyan" />
              Детали бизнеса
            </DialogTitle>
          </DialogHeader>
          
          {selectedBusiness && (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 bg-white/5 rounded-xl">
                <span className="text-4xl">{selectedBusiness.config?.icon}</span>
                <div>
                  <h3 className="text-xl font-bold text-white">
                    {selectedBusiness.config?.name?.ru}
                  </h3>
                  <div className="flex gap-2 mt-1">
                    <Badge className={TIER_COLORS[selectedBusiness.config?.tier || 1]}>
                      Tier {selectedBusiness.config?.tier}
                    </Badge>
                    <Badge variant="outline">Уровень {selectedBusiness.level}</Badge>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-white/5 rounded-lg">
                  <div className="text-xs text-text-muted">Прочность</div>
                  <div className="text-lg font-bold text-white">
                    {selectedBusiness.durability?.toFixed(1)}%
                  </div>
                </div>
                <div className="p-3 bg-white/5 rounded-lg">
                  <div className="text-xs text-text-muted">Доход/час</div>
                  <div className="text-lg font-bold text-green-400">
                    {selectedBusiness.production?.income_after_tax?.toFixed(2)} TON
                  </div>
                </div>
                <div className="p-3 bg-white/5 rounded-lg">
                  <div className="text-xs text-text-muted">Налог</div>
                  <div className="text-lg font-bold text-yellow-400">
                    {((selectedBusiness.production?.tax_rate || 0.15) * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="p-3 bg-white/5 rounded-lg">
                  <div className="text-xs text-text-muted">Склад</div>
                  <div className="text-lg font-bold text-white">
                    {selectedBusiness.storage?.capacity || 0}
                  </div>
                </div>
              </div>
              
              {selectedBusiness.patron && (
                <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Crown className="w-4 h-4 text-purple-400" />
                    <span className="text-purple-400 font-medium">Патрон</span>
                  </div>
                  <div className="text-white">
                    {selectedBusiness.patron.type} (Ур. {selectedBusiness.patron.level})
                  </div>
                  <div className="text-xs text-text-muted mt-1">
                    Бонус: +{((selectedBusiness.patron.bonus || 1) - 1) * 100}% к доходу
                  </div>
                </div>
              )}
              
              <div className="text-xs text-text-muted">
                ID: {selectedBusiness.id}
              </div>
              
              {/* Кнопка продажи */}
              <Button 
                onClick={() => {
                  setShowDetailsModal(false);
                  setShowSellModal(true);
                }}
                className="w-full bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30"
              >
                <Tag className="w-4 h-4 mr-2" />
                Выставить на продажу
              </Button>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailsModal(false)} className="border-white/10">
              Закрыть
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Sell Modal */}
      <Dialog open={showSellModal} onOpenChange={setShowSellModal}>
        <DialogContent className="bg-void border-red-500/20">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-white">
              <Tag className="w-5 h-5 text-red-400" />
              Продать бизнес
            </DialogTitle>
            <DialogDescription className="text-text-muted">
              Бизнес будет продан вместе с землёй. Укажите желаемую цену.
            </DialogDescription>
          </DialogHeader>
          
          {selectedBusiness && (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 bg-white/5 rounded-xl">
                <span className="text-4xl">{selectedBusiness.config?.icon}</span>
                <div>
                  <h3 className="text-lg font-bold text-white">
                    {selectedBusiness.config?.name?.ru}
                  </h3>
                  <Badge variant="outline">Уровень {selectedBusiness.level}</Badge>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label className="text-white">Цена продажи (TON)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0.1"
                  value={sellPrice}
                  onChange={(e) => {
                    setSellPrice(e.target.value);
                    if (e.target.value) calculateSaleTax(e.target.value);
                  }}
                  placeholder="Например: 10.00"
                  className="bg-white/5 border-white/10"
                />
              </div>
              
              {sellTaxInfo && (
                <div className="p-4 bg-white/5 rounded-xl space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-text-muted">Цена продажи:</span>
                    <span className="text-white">{sellTaxInfo.price} TON</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-text-muted">Налог ({sellTaxInfo.tax_rate_percent}):</span>
                    <span className="text-red-400">-{sellTaxInfo.tax_amount} TON</span>
                  </div>
                  <div className="h-px bg-white/10 my-2" />
                  <div className="flex justify-between font-bold">
                    <span className="text-white">Вы получите:</span>
                    <span className="text-green-400">{sellTaxInfo.seller_receives} TON</span>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowSellModal(false)} className="border-white/10">
              Отмена
            </Button>
            <Button 
              onClick={handleSellBusiness}
              disabled={!sellPrice || isSelling}
              className="bg-red-500 text-white hover:bg-red-600"
            >
              {isSelling ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Tag className="w-4 h-4 mr-2" />}
              Выставить на продажу
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
