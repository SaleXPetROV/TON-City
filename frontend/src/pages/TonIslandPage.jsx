import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Loader2, ZoomIn, ZoomOut, Home, Info, Building2,
  Coins, MapPin, X, ChevronRight, AlertCircle, Crown,
  RefreshCw, Play, Pause, TrendingUp, Building
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import Sidebar from '@/components/Sidebar';

// Import map engine
import IsometricMapEngine, { mapStore, hexToPixel, getZone, GRID_COLS, GRID_ROWS, BUILDING_ICONS } from '@/engine/IsometricMapEngine';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Tier colors
const TIER_STYLES = {
  1: 'bg-green-500/20 text-green-400 border-green-500/30',
  2: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  3: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
};

export default function TonIslandPage({ user }) {
  const navigate = useNavigate();
  const containerRef = useRef(null);
  const engineRef = useRef(null);
  
  const [isLoading, setIsLoading] = useState(true);
  const [businessTypes, setBusinessTypes] = useState({});
  const [patrons, setPatrons] = useState([]);
  const [userBalance, setUserBalance] = useState(0);
  
  // Modals
  const [selectedCell, setSelectedCell] = useState(null);
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);
  const [showBuildModal, setShowBuildModal] = useState(false);
  const [showBusinessModal, setShowBusinessModal] = useState(false);
  const [selectedBusinessType, setSelectedBusinessType] = useState('');
  const [selectedPatron, setSelectedPatron] = useState('');
  
  // Loading states
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  const [showBuildings, setShowBuildings] = useState(false);
  const [showBuildingsToast, setShowBuildingsToast] = useState(false);
  
  const token = localStorage.getItem('token');

  // Generate hexagonal grid cells
  const generateCells = useCallback(() => {
    const cells = [];
    const centerQ = Math.floor(GRID_COLS / 2);
    const centerR = Math.floor(GRID_ROWS / 2);
    
    for (let r = 0; r < GRID_ROWS; r++) {
      for (let q = 0; q < GRID_COLS; q++) {
        // Offset for hexagonal shape (island form)
        const dist = Math.abs(q - centerQ) + Math.abs(r - centerR);
        if (dist > Math.min(GRID_COLS, GRID_ROWS) * 0.6) continue; // Island shape
        
        const zone = getZone(q, r, centerQ, centerR);
        const basePrice = { core: 50, inner: 30, middle: 15, outer: 5 }[zone] || 5;
        
        cells.push({
          q,
          r,
          zone,
          price: basePrice,
          owner: null,
          building: null,
        });
      }
    }
    
    return cells;
  }, []);

  // Fetch island data from server
  const fetchIslandData = useCallback(async () => {
    try {
      const res = await fetch(`${API}/island`);
      if (res.ok) {
        const data = await res.json();
        
        // Convert server data to our cell format
        const cells = (data.cells || []).map(cell => ({
          q: cell.x,
          r: cell.y,
          zone: cell.zone,
          price: cell.price,
          owner: cell.owner,
          building: cell.business ? {
            type: cell.business.type || cell.business,
            level: cell.business.level || 1,
            tier: cell.business.tier || 1,
            is_active: cell.business.is_active !== false,
            durability: cell.business.durability || 100,
          } : null,
        }));
        
        // If server returns no cells, generate default grid
        if (cells.length === 0) {
          mapStore.dispatch({ type: 'SET_CELLS', cells: generateCells() });
        } else {
          mapStore.dispatch({ type: 'SET_CELLS', cells });
        }
      } else {
        // Fallback to generated cells
        mapStore.dispatch({ type: 'SET_CELLS', cells: generateCells() });
      }
    } catch (error) {
      console.error('Failed to fetch island:', error);
      // Fallback to generated cells
      mapStore.dispatch({ type: 'SET_CELLS', cells: generateCells() });
    }
  }, [generateCells]);

  // Fetch business types
  const fetchBusinessTypes = useCallback(async () => {
    try {
      const [typesRes, patronsRes] = await Promise.all([
        fetch(`${API}/businesses/types`).then(r => r.json()),
        fetch(`${API}/patrons`).then(r => r.json())
      ]);
      
      setBusinessTypes(typesRes.business_types || typesRes.businesses || typesRes || {});
      setPatrons(patronsRes.patrons || []);
    } catch (error) {
      console.error('Failed to fetch business types:', error);
    }
  }, []);

  // Initialize map engine
  useEffect(() => {
    if (!containerRef.current) return;
    
    // Prevent double initialization in React Strict Mode
    let isMounted = true;
    
    const initEngine = async () => {
      if (!isMounted) return;
      
      setIsLoading(true);
      
      try {
        // Set user in store
        if (user) {
          mapStore.dispatch({
            type: 'SET_USER',
            userId: user.id,
            userWallet: user.wallet_address
          });
          setUserBalance(user.balance_ton || 0);
        }
        
        // Destroy existing engine if any
        if (engineRef.current) {
          engineRef.current.destroy();
          engineRef.current = null;
        }
        
        // Create engine
        const rect = containerRef.current.getBoundingClientRect();
        
        const engine = new IsometricMapEngine(containerRef.current, {
          width: rect.width,
          height: rect.height,
          onCellClick: handleCellClick,
          onCellHover: handleCellHover,
        });
        
        await engine.init();
        
        if (!isMounted) {
          engine.destroy();
          return;
        }
        
        engineRef.current = engine;
        
        // Now fetch data AFTER engine is initialized and subscribed
        await fetchIslandData();
        await fetchBusinessTypes();
        
      } catch (error) {
        console.error('Error initializing map:', error);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };
    
    initEngine();
    
    return () => {
      isMounted = false;
      if (engineRef.current) {
        engineRef.current.destroy();
        engineRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current && engineRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        engineRef.current.resize(rect.width, rect.height);
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Handle cell click
  const handleCellClick = useCallback((cell) => {
    if (!cell) return;
    
    setSelectedCell(cell);
    
    if (cell.building) {
      setShowBusinessModal(true);
    } else if (!cell.owner) {
      setShowPurchaseModal(true);
    } else if (cell.owner === user?.id || cell.owner === user?.wallet_address) {
      setShowBuildModal(true);
    } else {
      // Show info about other player's cell
      toast.info(`Этот участок принадлежит другому игроку`);
    }
  }, [user]);

  // Handle cell hover
  const handleCellHover = useCallback((cell) => {
    // Optional: show tooltip or update UI
  }, []);

  // Update balance when user changes - ONLY if significantly different (e.g. initial load or top-up)
  useEffect(() => {
    if (user?.balance_ton !== undefined) {
      // Only update if difference is > 1 TON (to avoid overwriting optimistic updates with stale data)
      // or if current balance is 0 (initial load)
      if (Math.abs(userBalance - user.balance_ton) > 1 || userBalance === 0) {
        setUserBalance(user.balance_ton);
      }
    }
  }, [user?.balance_ton]);

  // Refresh balance periodically and after actions
  const refreshUserBalance = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUserBalance(data.balance_ton || 0);
      }
    } catch (error) {
      console.error('Failed to refresh balance:', error);
    }
  }, [token]);

  // Handle purchase with optimistic update + refresh
  const handlePurchase = async () => {
    if (!selectedCell || !token) return;
    
    setIsPurchasing(true);
    try {
      const res = await fetch(`${API}/island/buy/${selectedCell.q}/${selectedCell.r}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Purchase failed');
      }
      
      const data = await res.json();
      
      // Optimistic update
      const newBalance = data.new_balance !== undefined ? data.new_balance : (userBalance - selectedCell.price);
      setUserBalance(newBalance);
      
      // Update local state map
      mapStore.dispatch({
        type: 'UPDATE_CELL',
        cell: { ...selectedCell, owner: user?.id }
      });
      
      toast.success('Участок куплен!');
      setShowPurchaseModal(false);
      
      // Refresh real data in background
      refreshUserBalance();
      
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsPurchasing(false);
    }
  };

  // Build business
  const handleBuild = async () => {
    if (!selectedCell || !selectedBusinessType || !token) return;
    
    setIsBuilding(true);
    try {
      const res = await fetch(`${API}/island/build/${selectedCell.q}/${selectedCell.r}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          business_type: selectedBusinessType,
          patron_id: selectedPatron || null
        })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Build failed');
      }
      
      const data = await res.json();
      
      // Update local state
      const bizConfig = businessTypes[selectedBusinessType];
      mapStore.dispatch({
        type: 'UPDATE_CELL',
        cell: {
          ...selectedCell,
          building: {
            type: selectedBusinessType,
            level: 1,
            tier: bizConfig?.tier || 1,
            is_active: true
          }
        }
      });
      
      toast.success('Бизнес построен!');
      setShowBuildModal(false);
      setSelectedBusinessType('');
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsBuilding(false);
    }
  };

  // Zoom controls
  const handleZoomIn = () => {
    if (engineRef.current) {
      engineRef.current.zoomIn();
    }
  };

  const handleZoomOut = () => {
    if (engineRef.current) {
      engineRef.current.zoomOut();
    }
  };

  const handleResetCamera = () => {
    if (engineRef.current) {
      engineRef.current.resetCamera();
    }
  };

  // Refresh data
  const handleRefresh = async () => {
    setIsLoading(true);
    await fetchIslandData();
    await fetchBusinessTypes();
    setIsLoading(false);
    toast.success('Данные обновлены');
  };

  return (
    <div className="flex h-screen bg-void overflow-hidden">
      <Sidebar user={user} />
      
      <div className="flex-1 flex flex-col lg:ml-16 overflow-hidden">
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-white/10 bg-void/95 backdrop-blur-sm z-20">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-unbounded text-xl font-bold text-white flex items-center gap-2">
                <MapPin className="w-6 h-6 text-cyber-cyan" />
                ОСТРОВ TON
              </h1>
              <p className="text-text-muted text-sm">
                Изометрическая карта • Баланс: {userBalance.toFixed(2)} TON
              </p>
            </div>
            
            <Button 
              onClick={handleRefresh} 
              variant="outline" 
              size="sm" 
              className="border-white/10"
              disabled={isLoading}
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
            
            <Button
              data-testid="night-mode-toggle"
              onClick={() => {
                const isNight = !mapStore.getState().isNight;
                if (engineRef.current) engineRef.current.setNightMode(isNight);
              }}
              variant="outline"
              size="sm"
              className="ml-2 border-white/10 bg-indigo-900/20 text-indigo-300 hover:bg-indigo-900/40"
            >
              🌙
            </Button>
          </div>
        </div>

        {/* Map Container */}
        <div className="flex-1 relative overflow-hidden">
          {/* Pixi.js Canvas Container */}
          <div 
            ref={containerRef} 
            className="w-full h-full"
            style={{ touchAction: 'none' }}
          />
          
          {/* Loading Overlay */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-void/80 z-30">
              <div className="text-center">
                <Loader2 className="w-12 h-12 text-cyber-cyan animate-spin mx-auto mb-4" />
                <p className="text-white">Загрузка карты...</p>
              </div>
            </div>
          )}
          
          {/* Zoom Controls */}
          <div className="absolute bottom-4 right-4 flex flex-col gap-2 z-20">
            {/* Buildings Toggle Button */}
            <Button
              data-testid="buildings-toggle"
              onClick={() => {
                if (!showBuildings) {
                  setShowBuildingsToast(true);
                  toast.warning('В процессе разработки', {
                    description: 'Отображение зданий скоро будет доступно',
                    duration: 3000,
                  });
                  setTimeout(() => setShowBuildingsToast(false), 3000);
                } else {
                  setShowBuildings(false);
                }
              }}
              variant="outline"
              size="icon"
              className={`w-12 h-12 transition-all ${
                showBuildings 
                  ? 'bg-green-500/20 border-green-500 text-green-400 hover:bg-green-500/30' 
                  : 'bg-red-500/20 border-red-500 text-red-400 hover:bg-red-500/30'
              }`}
              title={showBuildings ? 'Скрыть здания' : 'Показать здания'}
            >
              <Building className="w-5 h-5" />
            </Button>
            
            <div className="h-2" />
            
            <Button
              onClick={handleZoomIn}
              variant="outline"
              size="icon"
              className="bg-black/60 border-white/20 hover:bg-black/80"
            >
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button
              onClick={handleZoomOut}
              variant="outline"
              size="icon"
              className="bg-black/60 border-white/20 hover:bg-black/80"
            >
              <ZoomOut className="w-4 h-4" />
            </Button>
            <Button
              onClick={handleResetCamera}
              variant="outline"
              size="icon"
              className="bg-black/60 border-white/20 hover:bg-black/80"
            >
              <Home className="w-4 h-4" />
            </Button>
          </div>

          {/* "В разработке" Toast Indicator */}
          <AnimatePresence>
            {showBuildingsToast && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="absolute bottom-24 right-4 z-30"
              >
                <div className="bg-yellow-500/90 text-black px-4 py-2 rounded-lg font-bold text-sm shadow-lg">
                  В процессе разработки
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Legend - City Island 3 Style (без цен) */}
          <div className="absolute top-4 left-4 bg-slate-900/90 backdrop-blur-md rounded-xl p-4 text-xs space-y-2 z-20 max-w-[160px] border border-slate-700/50 shadow-xl">
            <div className="font-bold text-white mb-2 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-sky-400" />
              Легенда
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm shadow-inner" style={{backgroundColor: '#4ade80'}} />
              <span className="text-white/90">Ваши участки</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm shadow-inner" style={{backgroundColor: '#c084fc'}} />
              <span className="text-white/90">Чужие участки</span>
            </div>
            <div className="h-px bg-slate-600/50 my-2" />
            <div className="text-sky-400/90 text-[10px] mb-1 font-semibold tracking-wide">СВОБОДНЫЕ ЗОНЫ:</div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm shadow-inner" style={{backgroundColor: '#7dd3fc'}} />
              <span className="text-white/80">Ядро</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm shadow-inner" style={{backgroundColor: '#60a5fa'}} />
              <span className="text-white/80">Центр</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm shadow-inner" style={{backgroundColor: '#3b82f6'}} />
              <span className="text-white/80">Средняя</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm shadow-inner" style={{backgroundColor: '#2563eb'}} />
              <span className="text-white/80">Внешняя</span>
            </div>
          </div>

          {/* Selected Cell Info */}
          {selectedCell && !showPurchaseModal && !showBuildModal && !showBusinessModal && (
            <div className="absolute top-4 right-4 bg-black/80 backdrop-blur-sm rounded-lg p-4 text-sm z-20 min-w-[180px]">
              <div className="text-cyber-cyan font-bold mb-2">
                Гекс [{selectedCell.q}, {selectedCell.r}]
              </div>
              <div className="space-y-1 text-white/80">
                <div>Зона: <span className="text-white capitalize">{selectedCell.zone}</span></div>
                <div>Цена: <span className="text-cyber-cyan">{selectedCell.price} TON</span></div>
                {selectedCell.building && (
                  <>
                    <div className="h-px bg-white/20 my-2" />
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{BUILDING_ICONS[selectedCell.building.type] || '🏢'}</span>
                      <span>Lvl {selectedCell.building.level}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Business Recommendations Panel */}
          {!selectedCell && (
            <div className="absolute top-4 right-4 bg-slate-900/95 backdrop-blur-md rounded-xl p-4 text-sm z-20 w-[280px] border border-slate-700/50 shadow-xl">
              <div className="font-bold text-white mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-400" />
                Рекомендации
              </div>
              
              {/* Best Business to Build */}
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 mb-3">
                <div className="text-green-400 font-semibold text-xs mb-2">🏆 ВЫГОДНЫЙ БИЗНЕС</div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">☀️</span>
                  <div>
                    <div className="text-white font-bold">Гелиос Солар</div>
                    <div className="text-gray-400 text-xs">Tier 1 • Энергия</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <div className="text-gray-400">Постройка</div>
                    <div className="text-white font-bold">5 TON</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Доход/день</div>
                    <div className="text-green-400 font-bold">~0.5 TON</div>
                  </div>
                </div>
              </div>
              
              {/* Investment Summary */}
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-gray-400">💰 Земля (внешняя)</span>
                  <span className="text-white">25 TON</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-gray-400">🏗️ Постройка</span>
                  <span className="text-white">5 TON</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-gray-400">📊 Доход/сутки</span>
                  <span className="text-green-400">~0.5 TON</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-gray-400">📅 Доход/месяц</span>
                  <span className="text-green-400">~15 TON</span>
                </div>
                <div className="flex justify-between items-center py-1 bg-amber-500/10 rounded px-2">
                  <span className="text-amber-400">⏱️ Окупаемость</span>
                  <span className="text-amber-300 font-bold">~60 дней</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Purchase Modal */}
      <Dialog open={showPurchaseModal} onOpenChange={setShowPurchaseModal}>
        <DialogContent className="bg-void border-cyber-cyan/30">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Coins className="w-5 h-5 text-cyber-cyan" />
              Купить участок
            </DialogTitle>
          </DialogHeader>
          
          {selectedCell && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/5 p-3 rounded-lg">
                  <div className="text-xs text-text-muted">Координаты</div>
                  <div className="text-white font-bold">[{selectedCell.q}, {selectedCell.r}]</div>
                </div>
                <div className="bg-white/5 p-3 rounded-lg">
                  <div className="text-xs text-text-muted">Зона</div>
                  <div className="text-white font-bold capitalize">{selectedCell.zone}</div>
                </div>
              </div>
              
              <div className="bg-cyber-cyan/10 p-4 rounded-lg border border-cyber-cyan/30">
                <div className="text-sm text-text-muted">Стоимость</div>
                <div className="text-2xl font-bold text-cyber-cyan">
                  {selectedCell.price} TON
                </div>
              </div>
              
              <div className="text-sm text-text-muted">
                Ваш баланс: <span className={userBalance >= selectedCell.price ? 'text-green-400' : 'text-red-400'}>
                  {userBalance.toFixed(2)} TON
                </span>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPurchaseModal(false)} className="border-white/10">
              Отмена
            </Button>
            <Button 
              onClick={handlePurchase}
              disabled={isPurchasing || userBalance < (selectedCell?.price || 0)}
              className="bg-cyber-cyan text-black"
            >
              {isPurchasing ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Coins className="w-4 h-4 mr-2" />}
              Купить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Build Modal */}
      <Dialog open={showBuildModal} onOpenChange={setShowBuildModal}>
        <DialogContent className="bg-void border-green-500/30 max-w-lg max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-green-400" />
              Построить бизнес
            </DialogTitle>
            <DialogDescription className="text-text-muted">
              Выберите тип бизнеса для строительства на участке [{selectedCell?.q}, {selectedCell?.r}]
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="max-h-[350px] pr-2">
            <div className="space-y-2">
              {Object.entries(businessTypes).map(([type, config]) => (
                <div
                  key={type}
                  onClick={() => setSelectedBusinessType(type)}
                  className={`p-3 rounded-lg cursor-pointer transition-all border ${
                    selectedBusinessType === type
                      ? 'bg-green-500/20 border-green-500/50'
                      : 'bg-white/5 border-transparent hover:bg-white/10 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{config.icon || BUILDING_ICONS[type] || '🏢'}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-white truncate">
                        {config.name?.ru || config.name?.en || type}
                      </div>
                      <div className="text-xs text-text-muted">
                        {config.base_cost_ton || config.cost || '?'} TON • {config.produces || 'TON'}
                      </div>
                    </div>
                    <Badge className={TIER_STYLES[config.tier] || TIER_STYLES[1]}>
                      T{config.tier}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
          
          {selectedBusinessType && patrons.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-white/10">
              <label className="text-sm text-text-muted">Выбрать патрона (бонусы)</label>
              <Select value={selectedPatron} onValueChange={setSelectedPatron}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue placeholder="Без патрона" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Без патрона</SelectItem>
                  {patrons.map(p => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.icon} {p.name} (Lvl {p.level})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBuildModal(false)} className="border-white/10">
              Отмена
            </Button>
            <Button 
              onClick={handleBuild}
              disabled={isBuilding || !selectedBusinessType}
              className="bg-green-500 text-black hover:bg-green-600"
            >
              {isBuilding ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Building2 className="w-4 h-4 mr-2" />}
              Построить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Business Info Modal */}
      <Dialog open={showBusinessModal} onOpenChange={setShowBusinessModal}>
        <DialogContent className="bg-void border-purple-500/30">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Info className="w-5 h-5 text-purple-400" />
              Информация о бизнесе
            </DialogTitle>
          </DialogHeader>
          
          {selectedCell?.building && (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 bg-white/5 rounded-xl">
                <span className="text-4xl">
                  {BUILDING_ICONS[selectedCell.building.type] || '🏢'}
                </span>
                <div className="flex-1">
                  <div className="text-xl font-bold text-white">
                    {businessTypes[selectedCell.building.type]?.name?.ru || selectedCell.building.type}
                  </div>
                  <div className="flex gap-2 mt-1">
                    <Badge className={TIER_STYLES[selectedCell.building.tier]}>
                      Tier {selectedCell.building.tier}
                    </Badge>
                    <Badge variant="outline">
                      Уровень {selectedCell.building.level}
                    </Badge>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/5 p-3 rounded-lg">
                  <div className="text-xs text-text-muted">Координаты</div>
                  <div className="text-white font-bold">[{selectedCell.q}, {selectedCell.r}]</div>
                </div>
                <div className="bg-white/5 p-3 rounded-lg">
                  <div className="text-xs text-text-muted">Прочность</div>
                  <div className="text-white">{selectedCell.building.durability?.toFixed(0) || 100}%</div>
                </div>
              </div>
              
              {selectedCell.building.is_active === false && (
                <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                  <div className="flex items-center gap-2 text-red-400">
                    <Pause className="w-4 h-4" />
                    <span className="font-bold">Бизнес остановлен</span>
                  </div>
                  <p className="text-sm text-red-300 mt-1">
                    Не хватает ресурсов для работы. Пополните склады.
                  </p>
                </div>
              )}
              
              {selectedCell.building.is_active !== false && (
                <div className="p-3 bg-green-500/20 border border-green-500/30 rounded-lg">
                  <div className="flex items-center gap-2 text-green-400">
                    <Play className="w-4 h-4" />
                    <span className="font-bold">Бизнес работает</span>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBusinessModal(false)} className="border-white/10">
              Закрыть
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
