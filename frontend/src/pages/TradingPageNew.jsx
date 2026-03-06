import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShoppingCart, Filter, Search, Plus, Minus, ArrowUpDown,
  Package, Coins, TrendingUp, AlertCircle, Loader2, X,
  Check, ChevronDown, Tag, RefreshCw, Handshake, Warehouse, ArrowDown, ArrowUp
} from 'lucide-react';
import PageHeader from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import Sidebar from '@/components/Sidebar';
import { RESOURCES, getResource, formatPrice, formatAmount } from '@/lib/resourceConfig';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

export default function TradingPage({ user }) {
  const navigate = useNavigate();
  const [listings, setListings] = useState([]);
  const [myListings, setMyListings] = useState([]);
  const [myResources, setMyResources] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('buy'); // 'buy' | 'sell' | 'my' | 'operations'
  
  // Operations (Cooperation) data
  const [operations, setOperations] = useState(null);
  const [operationsLoading, setOperationsLoading] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    resource: 'all',
    minPrice: '',
    maxPrice: '',
    minAmount: '',
    maxAmount: '',
    sortBy: 'price_asc'
  });
  const [showFilters, setShowFilters] = useState(false);
  
  // Sell modal
  const [showSellModal, setShowSellModal] = useState(false);
  const [sellResource, setSellResource] = useState('');
  const [sellAmount, setSellAmount] = useState('');
  const [sellPrice, setSellPrice] = useState('');
  const [isSelling, setIsSelling] = useState(false);
  
  // Buy modal
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [selectedListing, setSelectedListing] = useState(null);
  const [buyAmount, setBuyAmount] = useState('');
  const [isBuying, setIsBuying] = useState(false);
  
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    fetchData();
  }, [token]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [listingsRes, myListingsRes, resourcesRes] = await Promise.all([
        fetch(`${API}/market/listings`),
        fetch(`${API}/market/my-listings`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/my/resources`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      if (listingsRes.ok) {
        const data = await listingsRes.json();
        setListings(data.listings || []);
      }
      
      if (myListingsRes.ok) {
        const data = await myListingsRes.json();
        setMyListings(data.listings || []);
      }
      
      if (resourcesRes.ok) {
        const data = await resourcesRes.json();
        setMyResources(data.resources || {});
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter listings
  const filteredListings = useMemo(() => {
    let result = [...listings];
    
    // Filter by resource
    if (filters.resource !== 'all') {
      result = result.filter(l => l.resource_type === filters.resource);
    }
    
    // Filter by price
    if (filters.minPrice) {
      result = result.filter(l => l.price_per_unit >= parseFloat(filters.minPrice));
    }
    if (filters.maxPrice) {
      result = result.filter(l => l.price_per_unit <= parseFloat(filters.maxPrice));
    }
    
    // Filter by amount
    if (filters.minAmount) {
      result = result.filter(l => l.amount >= parseInt(filters.minAmount));
    }
    if (filters.maxAmount) {
      result = result.filter(l => l.amount <= parseInt(filters.maxAmount));
    }
    
    // Sort
    switch (filters.sortBy) {
      case 'price_asc':
        result.sort((a, b) => a.price_per_unit - b.price_per_unit);
        break;
      case 'price_desc':
        result.sort((a, b) => b.price_per_unit - a.price_per_unit);
        break;
      case 'amount_desc':
        result.sort((a, b) => b.amount - a.amount);
        break;
      case 'newest':
        result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        break;
    }
    
    return result;
  }, [listings, filters]);

  // Get available resources for selling
  const availableResources = useMemo(() => {
    return Object.entries(myResources)
      .filter(([_, amount]) => amount > 0)
      .map(([id, amount]) => ({ id, amount, ...getResource(id) }));
  }, [myResources]);

  // Handle sell
  const handleSell = async () => {
    if (!sellResource || !sellAmount || !sellPrice) {
      toast.error('Заполните все поля');
      return;
    }
    
    const amount = formatAmount(parseFloat(sellAmount));
    const price = formatPrice(parseFloat(sellPrice));
    
    if (amount <= 0 || price <= 0) {
      toast.error('Количество и цена должны быть больше 0');
      return;
    }
    
    const available = myResources[sellResource] || 0;
    if (amount > available) {
      toast.error(`Недостаточно ресурсов. Доступно: ${available}`);
      return;
    }
    
    setIsSelling(true);
    try {
      const res = await fetch(`${API}/market/list-resource`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          resource_type: sellResource,
          amount,
          price_per_unit: price
        })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка создания листинга');
      }
      
      toast.success('Ресурсы выставлены на продажу!');
      setShowSellModal(false);
      setSellResource('');
      setSellAmount('');
      setSellPrice('');
      fetchData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsSelling(false);
    }
  };

  // Handle buy
  const handleBuy = async () => {
    if (!selectedListing || !buyAmount) {
      toast.error('Укажите количество');
      return;
    }
    
    const amount = formatAmount(parseFloat(buyAmount));
    
    if (amount <= 0) {
      toast.error('Количество должно быть больше 0');
      return;
    }
    
    if (amount > selectedListing.amount) {
      toast.error(`Максимум: ${selectedListing.amount}`);
      return;
    }
    
    setIsBuying(true);
    try {
      const res = await fetch(`${API}/market/buy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          listing_id: selectedListing.id,
          amount
        })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка покупки');
      }
      
      const data = await res.json();
      toast.success(
        <div className="flex flex-col gap-1">
          <span className="font-bold">Покупка успешна!</span>
          <span className="text-sm">Получено: {amount} {getResource(selectedListing.resource_type).name}</span>
          <span className="text-sm text-amber-400">Оплачено: {formatPrice(data.total_paid)} TON</span>
        </div>
      );
      setShowBuyModal(false);
      setBuyAmount('');
      setSelectedListing(null);
      fetchData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsBuying(false);
    }
  };

  // Cancel listing
  const handleCancelListing = async (listingId) => {
    try {
      const res = await fetch(`${API}/market/cancel/${listingId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error('Ошибка отмены');
      
      toast.success('Листинг отменён');
      fetchData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  // Fetch operations data
  const fetchOperations = async () => {
    setOperationsLoading(true);
    try {
      const res = await fetch(`${API}/my/trade-operations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setOperations(data);
      }
    } catch (error) {
      console.error('Failed to load operations:', error);
    } finally {
      setOperationsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'operations' && !operations) {
      fetchOperations();
    }
  }, [activeTab]);

  // Apply filters
  const applyFilters = () => {
    setShowFilters(false);
    toast.success('Фильтры применены');
  };

  // Reset filters
  const resetFilters = () => {
    setFilters({
      resource: 'all',
      minPrice: '',
      maxPrice: '',
      minAmount: '',
      maxAmount: '',
      sortBy: 'price_asc'
    });
    toast.success('Фильтры сброшены');
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-void">
        <Sidebar user={user} />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-cyber-cyan" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-void">
      <Sidebar user={user} />
      
      <main className="flex-1 p-4 lg:p-6 pt-4 lg:pt-6 lg:ml-16">
        <div className="max-w-6xl mx-auto">
          {/* Header - Mobile Optimized */}
          <PageHeader
            icon={<ShoppingCart className="w-5 h-5 lg:w-6 lg:h-6 text-cyber-cyan" />}
            title="ТОРГОВЛЯ"
            rightContent={
              <div className="flex items-center gap-2">
                <Button onClick={() => setShowFilters(true)} variant="outline" size="sm" className="border-white/10">
                  <Filter className="w-4 h-4" />
                </Button>
                <Button onClick={() => setShowSellModal(true)} size="sm" className="bg-green-500 hover:bg-green-600">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            }
          />
          <p className="text-text-muted mt-1 mb-4 text-sm">Покупайте и продавайте ресурсы</p>

          {/* Tabs */}
          <div className="flex gap-2 mb-4 lg:mb-6 overflow-x-auto">
            <Button
              onClick={() => setActiveTab('buy')}
              variant={activeTab === 'buy' ? 'default' : 'outline'}
              className={activeTab === 'buy' ? 'bg-cyber-cyan text-black' : 'border-white/10'}
            >
              <ShoppingCart className="w-4 h-4 mr-2" />
              Купить ({filteredListings.length})
            </Button>
            <Button
              onClick={() => setActiveTab('my')}
              variant={activeTab === 'my' ? 'default' : 'outline'}
              className={activeTab === 'my' ? 'bg-amber-500 text-black' : 'border-white/10'}
            >
              <Tag className="w-4 h-4 mr-2" />
              Мои листинги ({myListings.length})
            </Button>
            <Button
              data-testid="operations-tab"
              onClick={() => setActiveTab('operations')}
              variant={activeTab === 'operations' ? 'default' : 'outline'}
              className={activeTab === 'operations' ? 'bg-purple-500 text-white' : 'border-white/10'}
            >
              <Handshake className="w-4 h-4 mr-2" />
              Кооперация
            </Button>
          </div>

          {/* Active filters */}
          {(filters.resource !== 'all' || filters.minPrice || filters.maxPrice) && (
            <div className="flex flex-wrap gap-2 mb-4">
              {filters.resource !== 'all' && (
                <Badge variant="outline" className="bg-white/5">
                  {getResource(filters.resource).icon} {getResource(filters.resource).name}
                  <X 
                    className="w-3 h-3 ml-1 cursor-pointer" 
                    onClick={() => setFilters(f => ({ ...f, resource: 'all' }))}
                  />
                </Badge>
              )}
              {filters.minPrice && (
                <Badge variant="outline" className="bg-white/5">
                  Мин. цена: {filters.minPrice} TON
                  <X 
                    className="w-3 h-3 ml-1 cursor-pointer" 
                    onClick={() => setFilters(f => ({ ...f, minPrice: '' }))}
                  />
                </Badge>
              )}
              {filters.maxPrice && (
                <Badge variant="outline" className="bg-white/5">
                  Макс. цена: {filters.maxPrice} TON
                  <X 
                    className="w-3 h-3 ml-1 cursor-pointer" 
                    onClick={() => setFilters(f => ({ ...f, maxPrice: '' }))}
                  />
                </Badge>
              )}
              <Button size="sm" variant="ghost" onClick={resetFilters}>
                <RefreshCw className="w-3 h-3 mr-1" /> Сбросить
              </Button>
            </div>
          )}

          {/* Content */}
          {activeTab === 'buy' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredListings.length === 0 ? (
                <div className="col-span-full text-center py-12 text-text-muted">
                  <Package className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Нет предложений по заданным фильтрам</p>
                </div>
              ) : (
                filteredListings.map(listing => {
                  const resource = getResource(listing.resource_type);
                  return (
                    <Card 
                      key={listing.id} 
                      className={`bg-void border ${resource.borderColor} hover:border-opacity-100 cursor-pointer transition-all`}
                      onClick={() => {
                        setSelectedListing(listing);
                        setBuyAmount(String(Math.min(listing.amount, 10)));
                        setShowBuyModal(true);
                      }}
                    >
                      <CardContent className="p-4">
                        {/* Resource header */}
                        <div className="flex items-center gap-3 mb-3">
                          <div className={`w-12 h-12 rounded-lg ${resource.bgColor} flex items-center justify-center text-2xl`}>
                            {resource.icon}
                          </div>
                          <div className="flex-1">
                            <div className={`font-bold ${resource.textColor}`}>{resource.name}</div>
                            <div className="text-xs text-text-muted">{listing.seller_username}</div>
                          </div>
                        </div>
                        
                        {/* Price & Amount */}
                        <div className="grid grid-cols-2 gap-2 mb-3">
                          <div className="bg-white/5 rounded-lg p-2 text-center">
                            <div className="text-xs text-text-muted">Цена</div>
                            <div className="font-bold text-cyber-cyan">{formatPrice(listing.price_per_unit)} TON</div>
                          </div>
                          <div className="bg-white/5 rounded-lg p-2 text-center">
                            <div className="text-xs text-text-muted">Кол-во</div>
                            <div className="font-bold text-white">{formatAmount(listing.amount)}</div>
                          </div>
                        </div>
                        
                        {/* Total */}
                        <div className="text-sm text-right text-text-muted">
                          Всего: <span className="text-white">{formatPrice(listing.amount * listing.price_per_unit)} TON</span>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          )}

          {activeTab === 'my' && (
            <div className="space-y-4">
              {myListings.length === 0 ? (
                <div className="text-center py-12 text-text-muted">
                  <Tag className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>У вас нет активных листингов</p>
                  <Button className="mt-4" onClick={() => setShowSellModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Выставить на продажу
                  </Button>
                </div>
              ) : (
                myListings.map(listing => {
                  const resource = getResource(listing.resource_type);
                  return (
                    <Card key={listing.id} className={`bg-void border ${resource.borderColor}`}>
                      <CardContent className="p-4 flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-lg ${resource.bgColor} flex items-center justify-center text-2xl`}>
                          {resource.icon}
                        </div>
                        <div className="flex-1">
                          <div className={`font-bold ${resource.textColor}`}>{resource.name}</div>
                          <div className="text-sm text-text-muted">
                            {formatAmount(listing.amount)} шт × {formatPrice(listing.price_per_unit)} TON
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-cyber-cyan">
                            {formatPrice(listing.amount * listing.price_per_unit)} TON
                          </div>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="mt-1 text-red-400 border-red-500/30"
                            onClick={() => handleCancelListing(listing.id)}
                          >
                            <X className="w-3 h-3 mr-1" /> Отменить
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          )}

          {/* Operations (Cooperation) Tab */}
          {activeTab === 'operations' && (
            <div className="space-y-4" data-testid="operations-content">
              {operationsLoading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
                </div>
              ) : operations ? (
                <>
                  {/* Shared Warehouse */}
                  <Card className="bg-void border-purple-500/30">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2 mb-4">
                        <Warehouse className="w-5 h-5 text-purple-400" />
                        <h3 className="text-lg font-bold text-white">Общий склад</h3>
                      </div>
                      
                      {/* Warehouse capacity bar */}
                      <div className="mb-4">
                        <div className="flex justify-between text-sm mb-2">
                          <span className="text-text-muted">Заполнено</span>
                          <span className={operations.warehouse.is_overflowing ? 'text-red-400 font-bold' : 'text-white'}>
                            {operations.warehouse.used} / {operations.warehouse.capacity}
                            {operations.warehouse.is_overflowing && (
                              <span className="ml-2 text-red-400">
                                (+{operations.warehouse.overflow} лишних)
                              </span>
                            )}
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-3">
                          <div 
                            className={`h-3 rounded-full transition-all ${
                              operations.warehouse.is_overflowing ? 'bg-red-500' : 
                              operations.warehouse.used / operations.warehouse.capacity > 0.8 ? 'bg-yellow-500' : 'bg-purple-500'
                            }`}
                            style={{ width: `${Math.min(100, operations.warehouse.capacity > 0 ? (operations.warehouse.used / operations.warehouse.capacity) * 100 : 0)}%` }}
                          />
                        </div>
                      </div>

                      {/* Overflow warning */}
                      {operations.warehouse.is_overflowing && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4">
                          <div className="flex items-start gap-2">
                            <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <div className="text-red-400 font-bold text-sm">Склад переполнен!</div>
                              <div className="text-red-300 text-xs mt-1">
                                Лишних единиц: <strong>{operations.warehouse.overflow}</strong>. 
                                Порча 50% от лишнего товара в день: <strong>-{operations.warehouse.spoilage_per_day} ед./день</strong>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Items in warehouse */}
                      {Object.keys(operations.warehouse.items).length > 0 ? (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                          {Object.entries(operations.warehouse.items).map(([resource, amount]) => {
                            const res = getResource(resource);
                            return (
                              <div key={resource} className={`p-3 rounded-lg bg-white/5 border ${res.borderColor || 'border-white/10'}`}>
                                <div className="flex items-center gap-2">
                                  <span className="text-xl">{res.icon}</span>
                                  <div>
                                    <div className="text-xs text-text-muted">{res.name}</div>
                                    <div className="text-white font-bold">{amount}</div>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <div className="text-center py-4 text-text-muted text-sm">
                          Склад пуст
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Buy/Sell History */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Bought */}
                    <Card className="bg-void border-green-500/30">
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2 mb-4">
                          <ArrowDown className="w-5 h-5 text-green-400" />
                          <h3 className="text-lg font-bold text-white">Куплено</h3>
                        </div>
                        {Object.keys(operations.operations.bought).length > 0 ? (
                          <div className="space-y-2">
                            {Object.entries(operations.operations.bought).map(([resource, amount]) => {
                              const res = getResource(resource);
                              return (
                                <div key={resource} className="flex items-center justify-between p-2 bg-green-500/5 rounded-lg">
                                  <div className="flex items-center gap-2">
                                    <span className="text-lg">{res.icon}</span>
                                    <span className="text-white">{res.name}</span>
                                  </div>
                                  <span className="text-green-400 font-bold font-mono">+{amount}</span>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="text-center py-4 text-text-muted text-sm">
                            Нет покупок
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {/* Sold */}
                    <Card className="bg-void border-amber-500/30">
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2 mb-4">
                          <ArrowUp className="w-5 h-5 text-amber-400" />
                          <h3 className="text-lg font-bold text-white">Продано</h3>
                        </div>
                        {Object.keys(operations.operations.sold).length > 0 ? (
                          <div className="space-y-2">
                            {Object.entries(operations.operations.sold).map(([resource, amount]) => {
                              const res = getResource(resource);
                              return (
                                <div key={resource} className="flex items-center justify-between p-2 bg-amber-500/5 rounded-lg">
                                  <div className="flex items-center gap-2">
                                    <span className="text-lg">{res.icon}</span>
                                    <span className="text-white">{res.name}</span>
                                  </div>
                                  <span className="text-amber-400 font-bold font-mono">{amount}</span>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="text-center py-4 text-text-muted text-sm">
                            Нет продаж
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>

                  <Button onClick={fetchOperations} variant="outline" size="sm" className="border-white/10">
                    <RefreshCw className="w-4 h-4 mr-2" /> Обновить данные
                  </Button>
                </>
              ) : (
                <div className="text-center py-12 text-text-muted">
                  <Handshake className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Нет данных</p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Filters Modal */}
      <Dialog open={showFilters} onOpenChange={setShowFilters}>
        <DialogContent className="bg-void border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Filter className="w-5 h-5 text-cyber-cyan" />
              Фильтры
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Resource filter with icons */}
            <div>
              <Label>Ресурс</Label>
              <Select value={filters.resource} onValueChange={(v) => setFilters(f => ({ ...f, resource: v }))}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue placeholder="Все ресурсы" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">
                    <div className="flex items-center gap-2">📦 Все ресурсы</div>
                  </SelectItem>
                  {Object.values(RESOURCES).map(r => (
                    <SelectItem key={r.id} value={r.id}>
                      <div className="flex items-center gap-2">
                        <span>{r.icon}</span>
                        <span>{r.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {/* Price range */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Мин. цена (TON)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  value={filters.minPrice}
                  onChange={(e) => setFilters(f => ({ ...f, minPrice: e.target.value }))}
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div>
                <Label>Макс. цена (TON)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="100.00"
                  value={filters.maxPrice}
                  onChange={(e) => setFilters(f => ({ ...f, maxPrice: e.target.value }))}
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
            
            {/* Amount range */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Мин. кол-во</Label>
                <Input
                  type="number"
                  min="1"
                  step="1"
                  placeholder="1"
                  value={filters.minAmount}
                  onChange={(e) => setFilters(f => ({ ...f, minAmount: e.target.value }))}
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div>
                <Label>Макс. кол-во</Label>
                <Input
                  type="number"
                  min="1"
                  step="1"
                  placeholder="1000"
                  value={filters.maxAmount}
                  onChange={(e) => setFilters(f => ({ ...f, maxAmount: e.target.value }))}
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
            
            {/* Sort */}
            <div>
              <Label>Сортировка</Label>
              <Select value={filters.sortBy} onValueChange={(v) => setFilters(f => ({ ...f, sortBy: v }))}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="price_asc">Цена (по возрастанию)</SelectItem>
                  <SelectItem value="price_desc">Цена (по убыванию)</SelectItem>
                  <SelectItem value="amount_desc">Количество (больше)</SelectItem>
                  <SelectItem value="newest">Новые</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={resetFilters} className="border-white/10">
              Сбросить
            </Button>
            <Button onClick={applyFilters} className="bg-cyber-cyan text-black">
              <Check className="w-4 h-4 mr-2" />
              Применить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Sell Modal */}
      <Dialog open={showSellModal} onOpenChange={setShowSellModal}>
        <DialogContent className="bg-void border-green-500/30">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Tag className="w-5 h-5 text-green-400" />
              Выставить на продажу
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {availableResources.length === 0 ? (
              <div className="text-center py-6 text-text-muted">
                <Package className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>У вас нет ресурсов для продажи</p>
              </div>
            ) : (
              <>
                {/* Resource selection */}
                <div>
                  <Label>Выберите ресурс</Label>
                  <Select value={sellResource} onValueChange={setSellResource}>
                    <SelectTrigger className="bg-white/5 border-white/10 h-14">
                      <SelectValue placeholder="Выберите ресурс..." />
                    </SelectTrigger>
                    <SelectContent>
                      {availableResources.map(r => (
                        <SelectItem key={r.id} value={r.id}>
                          <div className="flex items-center gap-3 py-1">
                            <span className="text-xl">{r.icon}</span>
                            <div>
                              <div className="font-medium">{r.name}</div>
                              <div className="text-xs text-text-muted">Доступно: {formatAmount(r.amount)}</div>
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                {sellResource && (
                  <>
                    <div className={`p-3 rounded-lg ${getResource(sellResource).bgColor} border ${getResource(sellResource).borderColor}`}>
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">{getResource(sellResource).icon}</span>
                        <div>
                          <div className="font-bold">{getResource(sellResource).name}</div>
                          <div className="text-sm text-text-muted">
                            Доступно: <span className="text-white font-bold">{formatAmount(myResources[sellResource] || 0)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label>Количество (целое число)</Label>
                        <Input
                          type="number"
                          min="1"
                          step="1"
                          max={myResources[sellResource] || 0}
                          placeholder="100"
                          value={sellAmount}
                          onChange={(e) => setSellAmount(e.target.value)}
                          className="bg-white/5 border-white/10"
                        />
                      </div>
                      <div>
                        <Label>Цена за 1 шт (TON)</Label>
                        <Input
                          type="number"
                          step="0.01"
                          min="0.01"
                          placeholder="0.01"
                          value={sellPrice}
                          onChange={(e) => setSellPrice(e.target.value)}
                          className="bg-white/5 border-white/10"
                        />
                      </div>
                    </div>
                    
                    {sellAmount && sellPrice && (
                      <div className="bg-white/5 rounded-lg p-3 text-center">
                        <div className="text-sm text-text-muted">Итого получите</div>
                        <div className="text-2xl font-bold text-green-400">
                          ~{formatPrice(formatAmount(parseFloat(sellAmount)) * formatPrice(parseFloat(sellPrice)) * 0.87)} TON
                        </div>
                        <div className="text-xs text-amber-400">13% налог с продажи</div>
                      </div>
                    )}
                  </>
                )}
              </>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSellModal(false)} className="border-white/10">
              Отмена
            </Button>
            <Button 
              onClick={handleSell}
              disabled={isSelling || !sellResource || !sellAmount || !sellPrice}
              className="bg-green-500 hover:bg-green-600"
            >
              {isSelling ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Check className="w-4 h-4 mr-2" />}
              Выставить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Buy Modal */}
      <Dialog open={showBuyModal} onOpenChange={setShowBuyModal}>
        <DialogContent className="bg-void border-cyber-cyan/30">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-cyber-cyan" />
              Купить ресурс
            </DialogTitle>
          </DialogHeader>
          
          {selectedListing && (
            <div className="space-y-4">
              {/* Resource info */}
              <div className={`p-4 rounded-lg ${getResource(selectedListing.resource_type).bgColor} border ${getResource(selectedListing.resource_type).borderColor}`}>
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{getResource(selectedListing.resource_type).icon}</span>
                  <div>
                    <div className={`font-bold text-lg ${getResource(selectedListing.resource_type).textColor}`}>
                      {getResource(selectedListing.resource_type).name}
                    </div>
                    <div className="text-sm text-text-muted">Продавец: {selectedListing.seller_username}</div>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/5 rounded-lg p-3">
                  <div className="text-xs text-text-muted">Цена за 1 шт</div>
                  <div className="font-bold text-cyber-cyan">{formatPrice(selectedListing.price_per_unit)} TON</div>
                </div>
                <div className="bg-white/5 rounded-lg p-3">
                  <div className="text-xs text-text-muted">Доступно</div>
                  <div className="font-bold text-white">{formatAmount(selectedListing.amount)}</div>
                </div>
              </div>
              
              <div>
                <Label>Сколько купить?</Label>
                <div className="flex items-center gap-2 mt-1">
                  <Button size="icon" variant="outline" onClick={() => setBuyAmount(String(Math.max(1, parseInt(buyAmount || 0) - 10)))}>
                    <Minus className="w-4 h-4" />
                  </Button>
                  <Input
                    type="number"
                    min="1"
                    max={selectedListing.amount}
                    step="1"
                    value={buyAmount}
                    onChange={(e) => setBuyAmount(e.target.value)}
                    className="bg-white/5 border-white/10 text-center"
                  />
                  <Button size="icon" variant="outline" onClick={() => setBuyAmount(String(Math.min(selectedListing.amount, parseInt(buyAmount || 0) + 10)))}>
                    <Plus className="w-4 h-4" />
                  </Button>
                  <Button variant="outline" onClick={() => setBuyAmount(String(selectedListing.amount))}>
                    Всё
                  </Button>
                </div>
              </div>
              
              {buyAmount && (
                <div className="bg-cyber-cyan/10 rounded-lg p-4 text-center border border-cyber-cyan/30">
                  <div className="text-sm text-text-muted">К оплате</div>
                  <div className="text-2xl font-bold text-cyber-cyan">
                    {formatPrice(formatAmount(parseFloat(buyAmount)) * selectedListing.price_per_unit)} TON
                  </div>
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBuyModal(false)} className="border-white/10">
              Отмена
            </Button>
            <Button 
              onClick={handleBuy}
              disabled={isBuying || !buyAmount}
              className="bg-cyber-cyan text-black"
            >
              {isBuying ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <ShoppingCart className="w-4 h-4 mr-2" />}
              Купить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
