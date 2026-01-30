import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Store, MapPin, Building2, Plus, ShoppingCart, Trash2,
  Filter, SortAsc, RefreshCw, Package, Coins, ArrowUpRight,
  ArrowDownRight, Search, X, Check, AlertCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import Sidebar from '@/components/Sidebar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const RESOURCE_INFO = {
  crops: { name: 'Урожай', icon: '🌾', color: 'text-yellow-400' },
  energy: { name: 'Энергия', icon: '⚡', color: 'text-blue-400' },
  materials: { name: 'Материалы', icon: '🏗️', color: 'text-gray-400' },
  fuel: { name: 'Топливо', icon: '🛢️', color: 'text-orange-400' },
  ore: { name: 'Руда', icon: '🪨', color: 'text-amber-600' },
  goods: { name: 'Товары', icon: '📦', color: 'text-purple-400' },
  refined_fuel: { name: 'Топливо+', icon: '⚗️', color: 'text-red-400' },
  steel: { name: 'Сталь', icon: '🔩', color: 'text-slate-400' },
  textiles: { name: 'Текстиль', icon: '🧵', color: 'text-pink-400' },
};

const BUSINESS_ICONS = {
  farm: '🌾',
  factory: '🏭',
  shop: '🏪',
  restaurant: '🍽️',
  bank: '🏦',
  power_plant: '⚡',
  quarry: '⛏️',
};

export default function MarketplacePage({ user }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('resources');
  const [isLoading, setIsLoading] = useState(true);
  
  // Data
  const [resourceListings, setResourceListings] = useState([]);
  const [landListings, setLandListings] = useState([]);
  const [myResourceListings, setMyResourceListings] = useState([]);
  const [myLandListings, setMyLandListings] = useState([]);
  const [myPlots, setMyPlots] = useState([]);
  const [myBusinesses, setMyBusinesses] = useState([]);
  const [cities, setCities] = useState([]);
  
  // Filters
  const [resourceFilter, setResourceFilter] = useState('all');
  const [cityFilter, setCityFilter] = useState('all');
  const [sortBy, setSortBy] = useState('price');
  
  // Modals
  const [showSellResourceModal, setShowSellResourceModal] = useState(false);
  const [showSellLandModal, setShowSellLandModal] = useState(false);
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [selectedListing, setSelectedListing] = useState(null);
  
  // Forms
  const [sellResourceForm, setSellResourceForm] = useState({
    business_id: '',
    resource_type: '',
    amount: 0,
    price_per_unit: 0
  });
  
  const [sellLandForm, setSellLandForm] = useState({
    plot_id: '',
    price: 0
  });
  
  const [buyAmount, setBuyAmount] = useState(0);

  const token = localStorage.getItem('token');

  const fetchData = async () => {
    setIsLoading(true);
    try {
      // Fetch all listings
      const [resListings, landList, myRes, myLand, citiesData] = await Promise.all([
        fetch(`${API}/market/listings`).then(r => r.json()),
        fetch(`${API}/market/land/listings`).then(r => r.json()),
        token ? fetch(`${API}/market/my-listings`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()) : { listings: [] },
        token ? fetch(`${API}/market/land/my-listings`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()) : { listings: [] },
        fetch(`${API}/cities`).then(r => r.json())
      ]);
      
      setResourceListings(resListings.listings || []);
      setLandListings(landList.listings || []);
      setMyResourceListings(myRes.listings || []);
      setMyLandListings(myLand.listings || []);
      setCities(citiesData.cities || []);
      
      // Fetch user's plots and businesses for selling
      if (token && user) {
        const plotsRes = await fetch(`${API}/users/me/plots`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).catch(() => ({ plots: [] }));
        const bizRes = await fetch(`${API}/users/me/businesses`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).catch(() => ({ businesses: [] }));
        setMyPlots(plotsRes.plots || []);
        setMyBusinesses(bizRes.businesses || []);
      }
    } catch (error) {
      console.error('Failed to fetch marketplace data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [user]);

  const handleBuyResource = async () => {
    if (!selectedListing || buyAmount <= 0) return;
    
    try {
      const res = await fetch(`${API}/market/buy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          listing_id: selectedListing.id,
          amount: buyAmount
        })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Purchase failed');
      }
      
      const data = await res.json();
      toast.success(`Куплено ${buyAmount} ${RESOURCE_INFO[selectedListing.resource_type]?.name || selectedListing.resource_type} за ${data.total_paid.toFixed(4)} TON`);
      setShowBuyModal(false);
      setSelectedListing(null);
      setBuyAmount(0);
      fetchData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleBuyLand = async (listing) => {
    if (!confirm(`Купить участок в ${listing.city_name} за ${listing.price} TON?`)) return;
    
    try {
      const res = await fetch(`${API}/market/land/buy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ listing_id: listing.id })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Purchase failed');
      }
      
      const data = await res.json();
      toast.success(`Участок куплен за ${data.total_paid} TON! ${data.has_business ? 'С бизнесом!' : ''}`);
      fetchData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleSellResource = async () => {
    if (!sellResourceForm.business_id || sellResourceForm.amount <= 0 || sellResourceForm.price_per_unit <= 0) {
      toast.error('Заполните все поля');
      return;
    }
    
    try {
      const res = await fetch(`${API}/market/list`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(sellResourceForm)
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Listing failed');
      }
      
      toast.success('Ресурсы выставлены на продажу!');
      setShowSellResourceModal(false);
      setSellResourceForm({ business_id: '', resource_type: '', amount: 0, price_per_unit: 0 });
      fetchData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleSellLand = async () => {
    if (!sellLandForm.plot_id || sellLandForm.price <= 0) {
      toast.error('Выберите участок и укажите цену');
      return;
    }
    
    try {
      const res = await fetch(`${API}/market/land/list`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(sellLandForm)
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Listing failed');
      }
      
      toast.success('Участок выставлен на продажу!');
      setShowSellLandModal(false);
      setSellLandForm({ plot_id: '', price: 0 });
      fetchData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleCancelListing = async (type, listingId) => {
    const endpoint = type === 'resource' ? `/market/listing/${listingId}` : `/market/land/listing/${listingId}`;
    
    try {
      const res = await fetch(`${API}${endpoint}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error('Failed to cancel');
      
      toast.success('Листинг отменён');
      fetchData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const filteredResourceListings = resourceListings.filter(l => 
    resourceFilter === 'all' || l.resource_type === resourceFilter
  );

  const filteredLandListings = landListings.filter(l =>
    cityFilter === 'all' || l.city_id === cityFilter
  );

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
                  <Store className="w-8 h-8 text-cyber-cyan" />
                  МАРКЕТПЛЕЙС
                </h1>
                <p className="text-text-muted mt-1">Торгуйте ресурсами и землёй с другими игроками</p>
              </div>
              
              <div className="flex gap-2">
                <Button 
                  onClick={fetchData} 
                  variant="outline" 
                  className="border-white/10"
                  disabled={isLoading}
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  Обновить
                </Button>
                
                {user && (
                  <div className="flex gap-2">
                    <Button 
                      onClick={() => setShowSellResourceModal(true)}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Продать ресурсы
                    </Button>
                    <Button 
                      onClick={() => setShowSellLandModal(true)}
                      className="bg-amber-600 hover:bg-amber-700"
                    >
                      <MapPin className="w-4 h-4 mr-2" />
                      Продать землю
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4">
              <Card className="glass-panel border-white/10">
                <CardContent className="p-4 flex items-center gap-3">
                  <Package className="w-8 h-8 text-cyber-cyan" />
                  <div>
                    <div className="text-2xl font-bold text-white">{resourceListings.length}</div>
                    <div className="text-xs text-text-muted">Ресурсов на продаже</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="glass-panel border-white/10">
                <CardContent className="p-4 flex items-center gap-3">
                  <MapPin className="w-8 h-8 text-amber-400" />
                  <div>
                    <div className="text-2xl font-bold text-white">{landListings.length}</div>
                    <div className="text-xs text-text-muted">Участков на продаже</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="glass-panel border-white/10">
                <CardContent className="p-4 flex items-center gap-3">
                  <ArrowUpRight className="w-8 h-8 text-green-400" />
                  <div>
                    <div className="text-2xl font-bold text-white">{myResourceListings.filter(l => l.status === 'active').length}</div>
                    <div className="text-xs text-text-muted">Моих ресурсов</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="glass-panel border-white/10">
                <CardContent className="p-4 flex items-center gap-3">
                  <Coins className="w-8 h-8 text-yellow-400" />
                  <div>
                    <div className="text-2xl font-bold text-white">{(user?.balance_ton || 0).toFixed(2)}</div>
                    <div className="text-xs text-text-muted">TON баланс</div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="bg-white/5 border border-white/10">
                <TabsTrigger value="resources" className="data-[state=active]:bg-cyber-cyan data-[state=active]:text-black">
                  <Package className="w-4 h-4 mr-2" />
                  Ресурсы
                </TabsTrigger>
                <TabsTrigger value="land" className="data-[state=active]:bg-amber-500 data-[state=active]:text-black">
                  <MapPin className="w-4 h-4 mr-2" />
                  Земля
                </TabsTrigger>
                <TabsTrigger value="my-listings" className="data-[state=active]:bg-green-500 data-[state=active]:text-black">
                  <Store className="w-4 h-4 mr-2" />
                  Мои листинги
                </TabsTrigger>
              </TabsList>

              {/* Resources Tab */}
              <TabsContent value="resources" className="mt-4">
                <div className="flex gap-4 mb-4">
                  <Select value={resourceFilter} onValueChange={setResourceFilter}>
                    <SelectTrigger className="w-48 bg-white/5 border-white/10">
                      <Filter className="w-4 h-4 mr-2" />
                      <SelectValue placeholder="Все ресурсы" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Все ресурсы</SelectItem>
                      {Object.entries(RESOURCE_INFO).map(([key, info]) => (
                        <SelectItem key={key} value={key}>{info.icon} {info.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  {filteredResourceListings.length === 0 ? (
                    <div className="col-span-3 text-center py-12 text-text-muted">
                      <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>Нет предложений ресурсов</p>
                    </div>
                  ) : (
                    filteredResourceListings.map(listing => (
                      <Card key={listing.id} className="glass-panel border-white/10 hover:border-cyber-cyan/50 transition-all">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex items-center gap-2">
                              <span className="text-2xl">{RESOURCE_INFO[listing.resource_type]?.icon || '📦'}</span>
                              <div>
                                <div className="font-bold text-white">{RESOURCE_INFO[listing.resource_type]?.name || listing.resource_type}</div>
                                <div className="text-xs text-text-muted">от {listing.seller_username}</div>
                              </div>
                            </div>
                            <Badge variant="outline" className="border-cyber-cyan/50 text-cyber-cyan">
                              {listing.amount} шт
                            </Badge>
                          </div>
                          
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-text-muted">Цена за единицу:</span>
                              <span className="text-cyber-cyan font-mono">{listing.price_per_unit.toFixed(4)} TON</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-text-muted">Всего:</span>
                              <span className="text-white font-mono">{listing.total_price.toFixed(4)} TON</span>
                            </div>
                          </div>
                          
                          <Button 
                            onClick={() => {
                              setSelectedListing(listing);
                              setBuyAmount(listing.amount);
                              setShowBuyModal(true);
                            }}
                            className="w-full mt-4 bg-cyber-cyan text-black hover:brightness-110"
                            disabled={!user || listing.seller_id === user?.wallet_address}
                          >
                            <ShoppingCart className="w-4 h-4 mr-2" />
                            Купить
                          </Button>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </TabsContent>

              {/* Land Tab */}
              <TabsContent value="land" className="mt-4">
                <div className="flex gap-4 mb-4">
                  <Select value={cityFilter} onValueChange={setCityFilter}>
                    <SelectTrigger className="w-48 bg-white/5 border-white/10">
                      <Filter className="w-4 h-4 mr-2" />
                      <SelectValue placeholder="Все города" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Все города</SelectItem>
                      {cities.map(city => (
                        <SelectItem key={city.id} value={city.id}>{city.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {filteredLandListings.length === 0 ? (
                    <div className="col-span-2 text-center py-12 text-text-muted">
                      <MapPin className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>Нет участков на продаже</p>
                    </div>
                  ) : (
                    filteredLandListings.map(listing => (
                      <Card key={listing.id} className="glass-panel border-white/10 hover:border-amber-500/50 transition-all">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <div className="font-bold text-white flex items-center gap-2">
                                <MapPin className="w-4 h-4 text-amber-400" />
                                Участок [{listing.x}, {listing.y}]
                              </div>
                              <div className="text-sm text-amber-400">{listing.city_name}</div>
                            </div>
                            <Badge variant="outline" className="border-amber-500/50 text-amber-400">
                              {listing.price.toFixed(2)} TON
                            </Badge>
                          </div>
                          
                          <div className="space-y-2 text-sm mb-4">
                            <div className="flex justify-between">
                              <span className="text-text-muted">Продавец:</span>
                              <span className="text-white">{listing.seller_username}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-text-muted">Изначальная цена:</span>
                              <span className="text-text-muted">{listing.original_price?.toFixed(4) || '—'} TON</span>
                            </div>
                            
                            {listing.business && (
                              <div className="mt-3 p-2 bg-green-500/10 border border-green-500/20 rounded-lg">
                                <div className="flex items-center gap-2 text-green-400 mb-1">
                                  <Building2 className="w-4 h-4" />
                                  <span className="font-bold">С бизнесом!</span>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-xs">
                                  <div>
                                    <span className="text-text-muted">Тип:</span>
                                    <div className="text-white">{BUSINESS_ICONS[listing.business.type]} {listing.business.type}</div>
                                  </div>
                                  <div>
                                    <span className="text-text-muted">Уровень:</span>
                                    <div className="text-white">Lv.{listing.business.level}</div>
                                  </div>
                                  <div>
                                    <span className="text-text-muted">Связи:</span>
                                    <div className="text-white">{listing.business.connections}</div>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                          
                          <Button 
                            onClick={() => handleBuyLand(listing)}
                            className="w-full bg-amber-500 text-black hover:brightness-110"
                            disabled={!user || listing.seller_id === user?.wallet_address}
                          >
                            <ShoppingCart className="w-4 h-4 mr-2" />
                            Купить участок
                          </Button>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </TabsContent>

              {/* My Listings Tab */}
              <TabsContent value="my-listings" className="mt-4">
                <div className="grid grid-cols-2 gap-6">
                  {/* My Resource Listings */}
                  <div>
                    <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                      <Package className="w-5 h-5 text-cyber-cyan" />
                      Мои ресурсы на продаже
                    </h3>
                    <div className="space-y-3">
                      {myResourceListings.filter(l => l.status === 'active').length === 0 ? (
                        <div className="text-center py-8 text-text-muted">
                          <Package className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">Нет активных листингов</p>
                        </div>
                      ) : (
                        myResourceListings.filter(l => l.status === 'active').map(listing => (
                          <Card key={listing.id} className="glass-panel border-white/10">
                            <CardContent className="p-3 flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <span className="text-xl">{RESOURCE_INFO[listing.resource_type]?.icon}</span>
                                <div>
                                  <div className="text-white font-medium">{listing.amount} {RESOURCE_INFO[listing.resource_type]?.name}</div>
                                  <div className="text-xs text-text-muted">{listing.price_per_unit.toFixed(4)} TON/шт</div>
                                </div>
                              </div>
                              <Button 
                                size="sm" 
                                variant="destructive"
                                onClick={() => handleCancelListing('resource', listing.id)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </CardContent>
                          </Card>
                        ))
                      )}
                    </div>
                  </div>

                  {/* My Land Listings */}
                  <div>
                    <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                      <MapPin className="w-5 h-5 text-amber-400" />
                      Мои участки на продаже
                    </h3>
                    <div className="space-y-3">
                      {myLandListings.filter(l => l.status === 'active').length === 0 ? (
                        <div className="text-center py-8 text-text-muted">
                          <MapPin className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">Нет активных листингов</p>
                        </div>
                      ) : (
                        myLandListings.filter(l => l.status === 'active').map(listing => (
                          <Card key={listing.id} className="glass-panel border-white/10">
                            <CardContent className="p-3 flex items-center justify-between">
                              <div>
                                <div className="text-white font-medium">
                                  [{listing.x}, {listing.y}] - {listing.city_name}
                                </div>
                                <div className="text-xs text-amber-400">{listing.price.toFixed(2)} TON</div>
                              </div>
                              <Button 
                                size="sm" 
                                variant="destructive"
                                onClick={() => handleCancelListing('land', listing.id)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </CardContent>
                          </Card>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </ScrollArea>
      </div>

      {/* Buy Resource Modal */}
      <Dialog open={showBuyModal} onOpenChange={setShowBuyModal}>
        <DialogContent className="bg-void border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-cyber-cyan" />
              Купить ресурсы
            </DialogTitle>
          </DialogHeader>
          
          {selectedListing && (
            <div className="space-y-4">
              <div className="p-4 bg-white/5 rounded-xl">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-3xl">{RESOURCE_INFO[selectedListing.resource_type]?.icon}</span>
                  <div>
                    <div className="text-white font-bold">{RESOURCE_INFO[selectedListing.resource_type]?.name}</div>
                    <div className="text-sm text-text-muted">от {selectedListing.seller_username}</div>
                  </div>
                </div>
                <div className="text-sm text-text-muted">
                  Доступно: {selectedListing.amount} шт по {selectedListing.price_per_unit.toFixed(4)} TON
                </div>
              </div>
              
              <div>
                <Label className="text-white">Количество</Label>
                <Input 
                  type="number"
                  value={buyAmount}
                  onChange={(e) => setBuyAmount(Math.min(parseFloat(e.target.value) || 0, selectedListing.amount))}
                  max={selectedListing.amount}
                  className="bg-white/5 border-white/10 text-white"
                />
              </div>
              
              <div className="p-3 bg-cyber-cyan/10 border border-cyber-cyan/20 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span className="text-text-muted">Итого к оплате:</span>
                  <span className="text-cyber-cyan font-bold font-mono">
                    {(buyAmount * selectedListing.price_per_unit).toFixed(4)} TON
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBuyModal(false)} className="border-white/10">
              Отмена
            </Button>
            <Button onClick={handleBuyResource} className="bg-cyber-cyan text-black">
              <Check className="w-4 h-4 mr-2" />
              Подтвердить покупку
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Sell Resource Modal */}
      <Dialog open={showSellResourceModal} onOpenChange={setShowSellResourceModal}>
        <DialogContent className="bg-void border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <ArrowUpRight className="w-5 h-5 text-green-400" />
              Продать ресурсы
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label className="text-white">Выберите бизнес</Label>
              <Select 
                value={sellResourceForm.business_id} 
                onValueChange={(v) => {
                  const biz = myBusinesses.find(b => b.id === v);
                  setSellResourceForm({
                    ...sellResourceForm,
                    business_id: v,
                    resource_type: biz?.produces || ''
                  });
                }}
              >
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue placeholder="Выберите бизнес" />
                </SelectTrigger>
                <SelectContent>
                  {myBusinesses.length === 0 ? (
                    <SelectItem value="none" disabled>У вас нет бизнесов</SelectItem>
                  ) : (
                    myBusinesses.map(biz => (
                      <SelectItem key={biz.id} value={biz.id}>
                        {BUSINESS_ICONS[biz.business_type]} {biz.business_type} (Lv.{biz.level})
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label className="text-white">Количество</Label>
              <Input 
                type="number"
                value={sellResourceForm.amount}
                onChange={(e) => setSellResourceForm({...sellResourceForm, amount: parseFloat(e.target.value) || 0})}
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
            
            <div>
              <Label className="text-white">Цена за единицу (TON)</Label>
              <Input 
                type="number"
                step="0.0001"
                value={sellResourceForm.price_per_unit}
                onChange={(e) => setSellResourceForm({...sellResourceForm, price_per_unit: parseFloat(e.target.value) || 0})}
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
            
            {sellResourceForm.amount > 0 && sellResourceForm.price_per_unit > 0 && (
              <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span className="text-text-muted">Всего получите (минус 10% налог):</span>
                  <span className="text-green-400 font-bold font-mono">
                    {(sellResourceForm.amount * sellResourceForm.price_per_unit * 0.9).toFixed(4)} TON
                  </span>
                </div>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSellResourceModal(false)} className="border-white/10">
              Отмена
            </Button>
            <Button onClick={handleSellResource} className="bg-green-600">
              <Plus className="w-4 h-4 mr-2" />
              Выставить на продажу
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Sell Land Modal */}
      <Dialog open={showSellLandModal} onOpenChange={setShowSellLandModal}>
        <DialogContent className="bg-void border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <MapPin className="w-5 h-5 text-amber-400" />
              Продать участок
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label className="text-white">Выберите участок</Label>
              <Select 
                value={sellLandForm.plot_id} 
                onValueChange={(v) => {
                  const plot = myPlots.find(p => p.id === v);
                  setSellLandForm({
                    ...sellLandForm,
                    plot_id: v,
                    price: plot?.price || 0.1
                  });
                }}
              >
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue placeholder="Выберите участок" />
                </SelectTrigger>
                <SelectContent>
                  {myPlots.length === 0 ? (
                    <SelectItem value="none" disabled>У вас нет участков</SelectItem>
                  ) : (
                    myPlots.map(plot => (
                      <SelectItem key={plot.id} value={plot.id}>
                        [{plot.x}, {plot.y}] - {plot.city_name || 'Город'} ({plot.price?.toFixed(4)} TON)
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label className="text-white">Цена продажи (TON)</Label>
              <Input 
                type="number"
                step="0.01"
                value={sellLandForm.price}
                onChange={(e) => setSellLandForm({...sellLandForm, price: parseFloat(e.target.value) || 0})}
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
            
            {sellLandForm.price > 0 && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span className="text-text-muted">Получите (минус 10% налог):</span>
                  <span className="text-amber-400 font-bold font-mono">
                    {(sellLandForm.price * 0.9).toFixed(4)} TON
                  </span>
                </div>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSellLandModal(false)} className="border-white/10">
              Отмена
            </Button>
            <Button onClick={handleSellLand} className="bg-amber-500 text-black">
              <Plus className="w-4 h-4 mr-2" />
              Выставить на продажу
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
