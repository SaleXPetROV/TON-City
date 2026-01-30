import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Building2, Package, Coins, TrendingUp, RefreshCw, 
  Settings2, Link2, Zap, ShoppingCart, ChevronRight,
  Play, Pause, Check, X, AlertCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import Sidebar from '@/components/Sidebar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const BUSINESS_INFO = {
  farm: { name: 'Ферма', icon: '🌾', produces: 'crops', color: 'text-yellow-400' },
  factory: { name: 'Завод', icon: '🏭', produces: 'goods', consumes: ['materials'], color: 'text-gray-400' },
  shop: { name: 'Магазин', icon: '🏪', produces: 'money', consumes: ['goods'], color: 'text-pink-400' },
  restaurant: { name: 'Ресторан', icon: '🍽️', produces: 'money', consumes: ['crops'], color: 'text-red-400' },
  bank: { name: 'Банк', icon: '🏦', produces: 'money', color: 'text-blue-400' },
  power_plant: { name: 'Электростанция', icon: '⚡', produces: 'energy', consumes: ['fuel'], color: 'text-cyan-400' },
  quarry: { name: 'Карьер', icon: '⛏️', produces: 'ore', color: 'text-amber-600' },
  refinery: { name: 'НПЗ', icon: '🛢️', produces: 'refined_fuel', consumes: ['ore'], color: 'text-orange-400' },
  textile: { name: 'Текстиль', icon: '🧵', produces: 'textiles', consumes: ['crops'], color: 'text-purple-400' },
  steel_mill: { name: 'Сталелитейный', icon: '🔩', produces: 'steel', consumes: ['ore', 'energy'], color: 'text-slate-400' },
};

const RESOURCE_NAMES = {
  crops: 'Урожай',
  energy: 'Энергия',
  materials: 'Материалы',
  fuel: 'Топливо',
  ore: 'Руда',
  goods: 'Товары',
  refined_fuel: 'Топливо+',
  steel: 'Сталь',
  textiles: 'Текстиль',
  money: 'Деньги'
};

export default function MyBusinessesPage({ user }) {
  const navigate = useNavigate();
  const [businesses, setBusinesses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [showAutomationModal, setShowAutomationModal] = useState(false);
  const [marketListings, setMarketListings] = useState([]);
  const [automationSettings, setAutomationSettings] = useState({});

  const token = localStorage.getItem('token');

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [bizRes, listingsRes] = await Promise.all([
        fetch(`${API}/users/me/businesses`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
        fetch(`${API}/market/listings`).then(r => r.json())
      ]);
      
      setBusinesses(bizRes.businesses || []);
      setMarketListings(listingsRes.listings || []);
      
      // Load automation settings from localStorage
      const saved = localStorage.getItem('automation_settings');
      if (saved) {
        setAutomationSettings(JSON.parse(saved));
      }
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
  }, [user]);

  const handleCollectIncome = async (businessId) => {
    try {
      const res = await fetch(`${API}/businesses/${businessId}/collect`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка сбора дохода');
      }
      
      const data = await res.json();
      toast.success(`Собрано ${data.collected?.toFixed(4) || 0} TON (налог: ${data.tax?.toFixed(4) || 0} TON)`);
      fetchData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleCollectAll = async () => {
    let totalCollected = 0;
    for (const biz of businesses) {
      try {
        const res = await fetch(`${API}/businesses/${biz.id}/collect`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          totalCollected += data.collected || 0;
        }
      } catch (e) {
        // Continue with others
      }
    }
    toast.success(`Всего собрано: ${totalCollected.toFixed(4)} TON`);
    fetchData();
  };

  const openAutomation = (business) => {
    setSelectedBusiness(business);
    setShowAutomationModal(true);
  };

  const toggleAutomation = (businessId, resourceType, enabled) => {
    const newSettings = {
      ...automationSettings,
      [businessId]: {
        ...automationSettings[businessId],
        [resourceType]: {
          enabled,
          maxPrice: automationSettings[businessId]?.[resourceType]?.maxPrice || 0.01
        }
      }
    };
    setAutomationSettings(newSettings);
    localStorage.setItem('automation_settings', JSON.stringify(newSettings));
    
    if (enabled) {
      toast.success(`Автозакупка ${RESOURCE_NAMES[resourceType]} включена`);
    } else {
      toast.info(`Автозакупка ${RESOURCE_NAMES[resourceType]} отключена`);
    }
  };

  const getSuppliers = (resourceType) => {
    return marketListings
      .filter(l => l.resource_type === resourceType && l.status === 'active')
      .sort((a, b) => a.price_per_unit - b.price_per_unit)
      .slice(0, 5);
  };

  const handleBuyFromSupplier = async (listing, amount) => {
    try {
      const res = await fetch(`${API}/market/buy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          listing_id: listing.id,
          amount: amount
        })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка покупки');
      }
      
      const data = await res.json();
      toast.success(`Куплено ${amount} ${RESOURCE_NAMES[listing.resource_type]} за ${data.total_paid.toFixed(4)} TON`);
      fetchData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const totalIncome = businesses.reduce((sum, b) => sum + (b.pending_income || 0), 0);

  return (
    <div className="flex h-screen bg-void">
      <Sidebar user={user} />
      
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="font-unbounded text-2xl font-bold text-white flex items-center gap-3">
                  <Building2 className="w-8 h-8 text-cyber-cyan" />
                  МОИ БИЗНЕСЫ
                </h1>
                <p className="text-text-muted mt-1">Управляйте своими предприятиями и автоматизируйте закупки</p>
              </div>
              
              <div className="flex gap-2">
                <Button onClick={fetchData} variant="outline" className="border-white/10" disabled={isLoading}>
                  <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  Обновить
                </Button>
                {businesses.length > 0 && (
                  <Button onClick={handleCollectAll} className="bg-green-600 hover:bg-green-700">
                    <Coins className="w-4 h-4 mr-2" />
                    Собрать всё
                  </Button>
                )}
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4">
              <Card className="glass-panel border-white/10">
                <CardContent className="p-4 flex items-center gap-3">
                  <Building2 className="w-8 h-8 text-cyber-cyan" />
                  <div>
                    <div className="text-2xl font-bold text-white">{businesses.length}</div>
                    <div className="text-xs text-text-muted">Всего бизнесов</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="glass-panel border-white/10">
                <CardContent className="p-4 flex items-center gap-3">
                  <Coins className="w-8 h-8 text-green-400" />
                  <div>
                    <div className="text-2xl font-bold text-white">{totalIncome.toFixed(4)}</div>
                    <div className="text-xs text-text-muted">К сбору (TON)</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="glass-panel border-white/10">
                <CardContent className="p-4 flex items-center gap-3">
                  <TrendingUp className="w-8 h-8 text-amber-400" />
                  <div>
                    <div className="text-2xl font-bold text-white">
                      {businesses.reduce((sum, b) => sum + (b.level || 1), 0)}
                    </div>
                    <div className="text-xs text-text-muted">Сумма уровней</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="glass-panel border-white/10">
                <CardContent className="p-4 flex items-center gap-3">
                  <Link2 className="w-8 h-8 text-purple-400" />
                  <div>
                    <div className="text-2xl font-bold text-white">
                      {businesses.reduce((sum, b) => sum + (b.connected_businesses?.length || 0), 0)}
                    </div>
                    <div className="text-xs text-text-muted">Всего связей</div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Businesses List */}
            {businesses.length === 0 ? (
              <div className="text-center py-16">
                <Building2 className="w-16 h-16 mx-auto mb-4 text-text-muted opacity-50" />
                <h3 className="text-xl font-bold text-white mb-2">У вас пока нет бизнесов</h3>
                <p className="text-text-muted mb-6">Купите участок земли и постройте свой первый бизнес</p>
                <Button onClick={() => navigate('/map')} className="bg-cyber-cyan text-black">
                  Перейти к карте
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {businesses.map(business => {
                  const info = BUSINESS_INFO[business.business_type] || {};
                  const consumes = info.consumes || [];
                  
                  return (
                    <Card key={business.id} className="glass-panel border-white/10 hover:border-cyber-cyan/30 transition-all">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-4">
                          <div className="flex items-center gap-3">
                            <span className="text-3xl">{info.icon || '🏢'}</span>
                            <div>
                              <div className={`font-bold text-lg ${info.color || 'text-white'}`}>
                                {info.name || business.business_type}
                              </div>
                              <div className="text-xs text-text-muted">
                                [{business.plot_x}, {business.plot_y}] • {business.city_name || 'Город'}
                              </div>
                            </div>
                          </div>
                          <Badge className="bg-cyber-cyan/20 text-cyber-cyan">
                            Lv.{business.level || 1}
                          </Badge>
                        </div>

                        <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
                          <div className="p-2 bg-white/5 rounded-lg">
                            <div className="text-text-muted text-xs">Производит</div>
                            <div className="text-white font-medium">
                              {RESOURCE_NAMES[info.produces] || info.produces || '—'}
                            </div>
                          </div>
                          <div className="p-2 bg-white/5 rounded-lg">
                            <div className="text-text-muted text-xs">Связи</div>
                            <div className="text-white font-medium">
                              {business.connected_businesses?.length || 0}
                            </div>
                          </div>
                          <div className="p-2 bg-white/5 rounded-lg">
                            <div className="text-text-muted text-xs">Опыт</div>
                            <div className="text-white font-medium">{business.xp || 0} XP</div>
                          </div>
                          <div className="p-2 bg-green-500/10 rounded-lg">
                            <div className="text-text-muted text-xs">К сбору</div>
                            <div className="text-green-400 font-medium">
                              {(business.pending_income || 0).toFixed(4)} TON
                            </div>
                          </div>
                        </div>

                        {consumes.length > 0 && (
                          <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                            <div className="text-xs text-amber-400 mb-2 flex items-center gap-1">
                              <Package className="w-3 h-3" />
                              Требует ресурсы:
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {consumes.map(res => (
                                <Badge key={res} variant="outline" className="border-amber-500/30 text-amber-300">
                                  {RESOURCE_NAMES[res] || res}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="flex gap-2">
                          <Button 
                            onClick={() => handleCollectIncome(business.id)}
                            className="flex-1 bg-green-600 hover:bg-green-700"
                            size="sm"
                          >
                            <Coins className="w-4 h-4 mr-1" />
                            Собрать
                          </Button>
                          {consumes.length > 0 && (
                            <Button 
                              onClick={() => openAutomation(business)}
                              variant="outline"
                              className="border-white/10"
                              size="sm"
                            >
                              <Settings2 className="w-4 h-4 mr-1" />
                              Закупки
                            </Button>
                          )}
                          <Button 
                            onClick={() => navigate(`/game/${business.city_id}`)}
                            variant="outline"
                            className="border-white/10"
                            size="sm"
                          >
                            <ChevronRight className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Automation Modal */}
      <Dialog open={showAutomationModal} onOpenChange={setShowAutomationModal}>
        <DialogContent className="bg-void border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Settings2 className="w-5 h-5 text-cyber-cyan" />
              Автоматизация закупок
            </DialogTitle>
          </DialogHeader>
          
          {selectedBusiness && (
            <div className="space-y-4">
              <div className="p-3 bg-white/5 rounded-lg flex items-center gap-3">
                <span className="text-2xl">{BUSINESS_INFO[selectedBusiness.business_type]?.icon}</span>
                <div>
                  <div className="font-bold text-white">{BUSINESS_INFO[selectedBusiness.business_type]?.name}</div>
                  <div className="text-xs text-text-muted">Уровень {selectedBusiness.level || 1}</div>
                </div>
              </div>

              {(BUSINESS_INFO[selectedBusiness.business_type]?.consumes || []).map(resourceType => {
                const suppliers = getSuppliers(resourceType);
                const isEnabled = automationSettings[selectedBusiness.id]?.[resourceType]?.enabled;
                
                return (
                  <div key={resourceType} className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Package className="w-4 h-4 text-amber-400" />
                        <span className="text-white font-medium">{RESOURCE_NAMES[resourceType]}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-text-muted">Автозакупка</span>
                        <Switch 
                          checked={isEnabled}
                          onCheckedChange={(v) => toggleAutomation(selectedBusiness.id, resourceType, v)}
                        />
                      </div>
                    </div>

                    {suppliers.length > 0 ? (
                      <div className="space-y-2">
                        <div className="text-xs text-text-muted">Доступные поставщики (по цене):</div>
                        {suppliers.map(listing => (
                          <div key={listing.id} className="flex items-center justify-between p-2 bg-white/5 rounded-lg">
                            <div>
                              <div className="text-sm text-white">{listing.seller_username}</div>
                              <div className="text-xs text-text-muted">
                                {listing.amount} шт • {listing.price_per_unit.toFixed(4)} TON/шт
                              </div>
                            </div>
                            <Button 
                              size="sm"
                              onClick={() => handleBuyFromSupplier(listing, Math.min(10, listing.amount))}
                              className="bg-cyber-cyan text-black"
                            >
                              <ShoppingCart className="w-3 h-3 mr-1" />
                              Купить
                            </Button>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-4 text-text-muted text-sm">
                        <AlertCircle className="w-6 h-6 mx-auto mb-2 opacity-50" />
                        Нет поставщиков на маркете
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAutomationModal(false)} className="border-white/10">
              Закрыть
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
