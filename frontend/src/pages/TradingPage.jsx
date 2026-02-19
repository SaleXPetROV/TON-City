import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTonWallet } from '@tonconnect/ui-react';
import { motion } from 'framer-motion';
import {
  TrendingUp, Package, Users, History, RefreshCw,
  ArrowUpDown, ShoppingCart, Handshake, Clock
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import {
  getCurrentUser,
  getAllBusinesses,
  getBusinessTypes,
  getUserContracts,
  createContract,
  spotTrade,
  acceptContract
} from '@/lib/api';

const RESOURCE_INFO = {
  crops: { name: 'Урожай', icon: '🌾', basePrice: 0.001 },
  energy: { name: 'Энергия', icon: '⚡', basePrice: 0.0002 },
  materials: { name: 'Материалы', icon: '🏗️', basePrice: 0.005 },
  fuel: { name: 'Топливо', icon: '🛢️', basePrice: 0.008 },
  ore: { name: 'Руда', icon: '🪨', basePrice: 0.006 },
  goods: { name: 'Товары', icon: '📦', basePrice: 0.004 },
  refined_fuel: { name: 'Переработанное топливо', icon: '⚗️', basePrice: 0.015 },
  steel: { name: 'Сталь', icon: '🔩', basePrice: 0.012 },
  textiles: { name: 'Текстиль', icon: '🧵', basePrice: 0.003 },
};

export default function TradingPage() {
  const navigate = useNavigate();
  const wallet = useTonWallet();
  
  const [user, setUser] = useState(null);
  const [businesses, setBusinesses] = useState([]);
  const [myBusinesses, setMyBusinesses] = useState([]);
  const [businessTypes, setBusinessTypes] = useState({});
  const [contracts, setContracts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Modals
  const [showContractModal, setShowContractModal] = useState(false);
  const [showSpotTradeModal, setShowSpotTradeModal] = useState(false);
  
  // Contract form
  const [contractForm, setContractForm] = useState({
    sellerBusinessId: '',
    buyerBusinessId: '',
    resourceType: '',
    amountPerHour: 0,
    pricePerUnit: 0,
    durationDays: 7
  });
  
  // Spot trade form
  const [spotTradeForm, setSpotTradeForm] = useState({
    sellerBusinessId: '',
    buyerBusinessId: '',
    resourceType: '',
    amount: 0
  });
  
  useEffect(() => {
    // Проверяем авторизацию через token или wallet
    const token = localStorage.getItem('token');
    if (!token && !wallet?.account) {
      navigate('/auth?mode=login');
      return;
    }
    loadData();
  }, [wallet]);
  
  const loadData = async () => {
    setIsLoading(true);
    try {
      const [userData, businessesData, typesData, contractsData] = await Promise.all([
        getCurrentUser(),
        getAllBusinesses(),
        getBusinessTypes(),
        getUserContracts().catch(() => ({ contracts: [] }))
      ]);
      
      setUser(userData);
      setBusinesses(businessesData.businesses || []);
      setMyBusinesses((businessesData.businesses || []).filter(b => b.owner === wallet.account.address));
      setBusinessTypes(typesData.business_types || {});
      setContracts(contractsData.contracts || []);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleCreateContract = async () => {
    try {
      await createContract(contractForm);
      toast.success('Контракт создан! Ожидает подтверждения покупателя');
      setShowContractModal(false);
      loadData();
    } catch (error) {
      toast.error('Ошибка создания контракта');
    }
  };
  
  const handleSpotTrade = async () => {
    try {
      const result = await spotTrade(spotTradeForm);
      toast.success(`Сделка выполнена! ${result.seller_receives} TON`);
      setShowSpotTradeModal(false);
      loadData();
    } catch (error) {
      toast.error('Ошибка выполнения сделки');
    }
  };
  
  const handleAcceptContract = async (contractId) => {
    try {
      await acceptContract(contractId);
      toast.success('Контракт принят!');
      loadData();
    } catch (error) {
      toast.error('Ошибка принятия контракта');
    }
  };
  
  // Get available resources from businesses
  const getAvailableResources = () => {
    const resources = {};
    businesses.forEach(business => {
      const bt = businessTypes[business.business_type];
      if (bt?.produces && bt.produces !== 'none') {
        if (!resources[bt.produces]) {
          resources[bt.produces] = [];
        }
        resources[bt.produces].push(business);
      }
    });
    return resources;
  };
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-neon-blue mx-auto mb-4" />
          <p className="text-gray-400">Загрузка торговой площадки...</p>
        </div>
      </div>
    );
  }
  
  const availableResources = getAvailableResources();
  
  return (
    <div className="min-h-screen bg-void">
      {/* Header */}
      <header className="border-b border-white/10 bg-void/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={() => navigate('/game')}
                className="text-gray-400 hover:text-white"
              >
                ← Назад к игре
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-6 h-6 text-neon-blue" />
                  Торговая площадка
                </h1>
                <p className="text-sm text-gray-400">Торговля ресурсами между игроками</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-gray-400">Баланс</p>
                <p className="text-lg font-bold text-neon-blue">{user?.balance_ton?.toFixed(2) || '0.00'} TON</p>
              </div>
              <Button onClick={loadData} variant="outline" size="sm">
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs defaultValue="market" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-white/5">
            <TabsTrigger value="market" data-testid="market-tab">
              <Package className="w-4 h-4 mr-2" />
              Рынок ресурсов
            </TabsTrigger>
            <TabsTrigger value="contracts" data-testid="contracts-tab">
              <Handshake className="w-4 h-4 mr-2" />
              Контракты
            </TabsTrigger>
            <TabsTrigger value="my-resources" data-testid="my-resources-tab">
              <Users className="w-4 h-4 mr-2" />
              Мои ресурсы
            </TabsTrigger>
            <TabsTrigger value="history" data-testid="history-tab">
              <History className="w-4 h-4 mr-2" />
              История сделок
            </TabsTrigger>
          </TabsList>
          
          {/* Market Tab */}
          <TabsContent value="market" className="space-y-6">
            <div className="grid gap-4">
              <Card className="bg-white/5 border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ShoppingCart className="w-5 h-5" />
                    Доступные ресурсы
                  </CardTitle>
                  <CardDescription>Ресурсы от всех игроков</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {Object.entries(availableResources).map(([resource, providers]) => {
                      const info = RESOURCE_INFO[resource] || { name: resource, icon: '📦', basePrice: 0.001 };
                      return (
                        <Card key={resource} className="bg-white/5 border-white/10" data-testid={`resource-card-${resource}`}>
                          <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                              <span className="text-2xl">{info.icon}</span>
                              {info.name}
                            </CardTitle>
                            <CardDescription>
                              Базовая цена: {info.basePrice} TON/ед.
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            <p className="text-sm text-gray-400 mb-3">
                              Поставщики: {providers.length}
                            </p>
                            <Button
                              onClick={() => {
                                setSpotTradeForm(prev => ({ ...prev, resourceType: resource }));
                                setShowSpotTradeModal(true);
                              }}
                              className="w-full"
                              size="sm"
                              data-testid={`buy-${resource}-btn`}
                            >
                              <ShoppingCart className="w-4 h-4 mr-2" />
                              Купить
                            </Button>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                  
                  {Object.keys(availableResources).length === 0 && (
                    <div className="text-center py-12">
                      <Package className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                      <p className="text-gray-400">Пока нет доступных ресурсов</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
            
            <div className="grid gap-4 md:grid-cols-2">
              <Card className="bg-neon-blue/10 border-neon-blue/30">
                <CardHeader>
                  <CardTitle>Спотовая торговля</CardTitle>
                  <CardDescription>Мгновенная покупка/продажа ресурсов</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={() => setShowSpotTradeModal(true)}
                    className="w-full"
                    data-testid="spot-trade-btn"
                  >
                    <ArrowUpDown className="w-4 h-4 mr-2" />
                    Создать сделку
                  </Button>
                </CardContent>
              </Card>
              
              <Card className="bg-neon-purple/10 border-neon-purple/30">
                <CardHeader>
                  <CardTitle>Долгосрочные контракты</CardTitle>
                  <CardDescription>Автоматическая поставка ресурсов</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={() => setShowContractModal(true)}
                    className="w-full"
                    data-testid="create-contract-btn"
                  >
                    <Handshake className="w-4 h-4 mr-2" />
                    Создать контракт
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          
          {/* Contracts Tab */}
          <TabsContent value="contracts" className="space-y-4">
            <Card className="bg-white/5 border-white/10">
              <CardHeader>
                <CardTitle>Мои контракты</CardTitle>
                <CardDescription>Активные и ожидающие контракты</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[500px]">
                  {contracts.length > 0 ? (
                    <div className="space-y-3">
                      {contracts.map((contract) => {
                        const resource = RESOURCE_INFO[contract.resource_type] || {};
                        const isMyContract = contract.seller_id === wallet?.account?.address;
                        const isPending = !contract.is_active;
                        
                        return (
                          <Card key={contract.id} className="bg-white/5 border-white/10" data-testid={`contract-${contract.id}`}>
                            <CardContent className="pt-6">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <span className="text-3xl">{resource.icon || '📦'}</span>
                                  <div>
                                    <p className="font-semibold">{resource.name || contract.resource_type}</p>
                                    <p className="text-sm text-gray-400">
                                      {contract.amount_per_hour} ед/час × {contract.price_per_unit} TON
                                    </p>
                                  </div>
                                </div>
                                
                                <div className="text-right">
                                  <Badge variant={isPending ? "secondary" : "default"}>
                                    {isPending ? 'Ожидает' : 'Активен'}
                                  </Badge>
                                  {!isMyContract && isPending && (
                                    <Button
                                      size="sm"
                                      className="mt-2"
                                      onClick={() => handleAcceptContract(contract.id)}
                                      data-testid={`accept-contract-${contract.id}`}
                                    >
                                      Принять
                                    </Button>
                                  )}
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Handshake className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                      <p className="text-gray-400">У вас пока нет контрактов</p>
                      <Button
                        onClick={() => setShowContractModal(true)}
                        className="mt-4"
                      >
                        Создать контракт
                      </Button>
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* My Resources Tab */}
          <TabsContent value="my-resources" className="space-y-4">
            <Card className="bg-white/5 border-white/10">
              <CardHeader>
                <CardTitle>Мои бизнесы и ресурсы</CardTitle>
                <CardDescription>Ваши производства и запасы</CardDescription>
              </CardHeader>
              <CardContent>
                {myBusinesses.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    {myBusinesses.map((business) => {
                      const bt = businessTypes[business.business_type] || {};
                      const resource = bt.produces ? RESOURCE_INFO[bt.produces] : null;
                      
                      return (
                        <Card key={business.id} className="bg-white/5 border-white/10" data-testid={`my-business-${business.id}`}>
                          <CardContent className="pt-6">
                            <div className="flex items-center gap-3 mb-3">
                              <span className="text-2xl">{business.business_icon}</span>
                              <div>
                                <p className="font-semibold">{business.business_name}</p>
                                <p className="text-sm text-gray-400">Уровень {business.level}</p>
                              </div>
                            </div>
                            
                            {resource && (
                              <div className="mt-3 p-3 bg-white/5 rounded-lg">
                                <p className="text-sm text-gray-400">Производит:</p>
                                <p className="font-semibold flex items-center gap-2">
                                  {resource.icon} {resource.name}
                                </p>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Package className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">У вас пока нет бизнесов</p>
                    <Button onClick={() => navigate('/game')} className="mt-4">
                      Начать строительство
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* History Tab */}
          <TabsContent value="history" className="space-y-4">
            <Card className="bg-white/5 border-white/10">
              <CardHeader>
                <CardTitle>История сделок</CardTitle>
                <CardDescription>Последние торговые операции</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12">
                  <Clock className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">История сделок будет отображаться здесь</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
      
      {/* Create Contract Modal */}
      <Dialog open={showContractModal} onOpenChange={setShowContractModal}>
        <DialogContent className="bg-void border-white/10 text-white" data-testid="contract-modal">
          <DialogHeader>
            <DialogTitle>Создать контракт на поставку</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Мой бизнес (продавец)</Label>
              <Select
                onValueChange={(value) => setContractForm(prev => ({ ...prev, sellerBusinessId: value }))}
              >
                <SelectTrigger data-testid="seller-business-select">
                  <SelectValue placeholder="Выберите бизнес" />
                </SelectTrigger>
                <SelectContent>
                  {myBusinesses.map(b => {
                    const bt = businessTypes[b.business_type] || {};
                    if (bt.produces && bt.produces !== 'none') {
                      return (
                        <SelectItem key={b.id} value={b.id}>
                          {b.business_icon} {b.business_name}
                        </SelectItem>
                      );
                    }
                    return null;
                  })}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Покупатель (бизнес)</Label>
              <Select
                onValueChange={(value) => setContractForm(prev => ({ ...prev, buyerBusinessId: value }))}
              >
                <SelectTrigger data-testid="buyer-business-select">
                  <SelectValue placeholder="Выберите покупателя" />
                </SelectTrigger>
                <SelectContent>
                  {businesses
                    .filter(b => b.owner !== wallet?.account?.address)
                    .map(b => (
                      <SelectItem key={b.id} value={b.id}>
                        {b.business_icon} {b.business_name} ({b.owner.slice(0, 8)}...)
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Ресурс</Label>
              <Select
                onValueChange={(value) => setContractForm(prev => ({ ...prev, resourceType: value }))}
              >
                <SelectTrigger data-testid="resource-select">
                  <SelectValue placeholder="Выберите ресурс" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(RESOURCE_INFO).map(([key, info]) => (
                    <SelectItem key={key} value={key}>
                      {info.icon} {info.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Количество в час</Label>
              <Input
                type="number"
                value={contractForm.amountPerHour}
                onChange={(e) => setContractForm(prev => ({ ...prev, amountPerHour: parseFloat(e.target.value) }))}
                data-testid="amount-per-hour-input"
              />
            </div>
            
            <div>
              <Label>Цена за единицу (TON)</Label>
              <Input
                type="number"
                step="0.0001"
                value={contractForm.pricePerUnit}
                onChange={(e) => setContractForm(prev => ({ ...prev, pricePerUnit: parseFloat(e.target.value) }))}
                data-testid="price-per-unit-input"
              />
            </div>
            
            <div>
              <Label>Длительность (дней)</Label>
              <Input
                type="number"
                value={contractForm.durationDays}
                onChange={(e) => setContractForm(prev => ({ ...prev, durationDays: parseInt(e.target.value) }))}
                data-testid="duration-days-input"
              />
            </div>
            
            <Button
              onClick={handleCreateContract}
              className="w-full"
              data-testid="submit-contract-btn"
            >
              Создать контракт
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Spot Trade Modal */}
      <Dialog open={showSpotTradeModal} onOpenChange={setShowSpotTradeModal}>
        <DialogContent className="bg-void border-white/10 text-white" data-testid="spot-trade-modal">
          <DialogHeader>
            <DialogTitle>Спотовая сделка</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Продавец (бизнес)</Label>
              <Select
                onValueChange={(value) => setSpotTradeForm(prev => ({ ...prev, sellerBusinessId: value }))}
              >
                <SelectTrigger data-testid="spot-seller-select">
                  <SelectValue placeholder="Выберите продавца" />
                </SelectTrigger>
                <SelectContent>
                  {businesses.map(b => {
                    const bt = businessTypes[b.business_type] || {};
                    if (bt.produces && bt.produces !== 'none') {
                      return (
                        <SelectItem key={b.id} value={b.id}>
                          {b.business_icon} {b.business_name} ({b.owner.slice(0, 8)}...)
                        </SelectItem>
                      );
                    }
                    return null;
                  })}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Покупатель (мой бизнес)</Label>
              <Select
                onValueChange={(value) => setSpotTradeForm(prev => ({ ...prev, buyerBusinessId: value }))}
              >
                <SelectTrigger data-testid="spot-buyer-select">
                  <SelectValue placeholder="Выберите свой бизнес" />
                </SelectTrigger>
                <SelectContent>
                  {myBusinesses.map(b => (
                    <SelectItem key={b.id} value={b.id}>
                      {b.business_icon} {b.business_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Ресурс</Label>
              <Select
                value={spotTradeForm.resourceType}
                onValueChange={(value) => setSpotTradeForm(prev => ({ ...prev, resourceType: value }))}
              >
                <SelectTrigger data-testid="spot-resource-select">
                  <SelectValue placeholder="Выберите ресурс" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(RESOURCE_INFO).map(([key, info]) => (
                    <SelectItem key={key} value={key}>
                      {info.icon} {info.name} ({info.basePrice} TON/ед.)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Количество</Label>
              <Input
                type="number"
                value={spotTradeForm.amount}
                onChange={(e) => setSpotTradeForm(prev => ({ ...prev, amount: parseFloat(e.target.value) }))}
                data-testid="spot-amount-input"
              />
            </div>
            
            {spotTradeForm.resourceType && spotTradeForm.amount > 0 && (
              <div className="p-3 bg-neon-blue/10 rounded-lg">
                <p className="text-sm text-gray-400">Приблизительная стоимость:</p>
                <p className="text-lg font-bold text-neon-blue">
                  {(RESOURCE_INFO[spotTradeForm.resourceType]?.basePrice * spotTradeForm.amount).toFixed(2)} TON
                </p>
              </div>
            )}
            
            <Button
              onClick={handleSpotTrade}
              className="w-full"
              data-testid="submit-spot-trade-btn"
            >
              Выполнить сделку
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
