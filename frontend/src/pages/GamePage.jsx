import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Stage, Layer, Rect, Group, Text } from 'react-konva';
import { 
  MapPin, Building2, Wallet, X, ChevronLeft, ChevronRight,
  ZoomIn, ZoomOut, Home, RefreshCw, Loader2, TrendingUp, 
  ArrowDownToLine, ArrowUpFromLine, Users
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { DepositModal, WithdrawModal } from '@/components/BalanceModals';
import { 
  getAllPlots, getPlotByCoords, purchasePlot, confirmPlotPurchase,
  getBusinessTypes, buildBusiness, confirmBusinessBuild, getCurrentUser,
  tonToNano
} from '@/lib/api';
import { toast } from 'sonner';
import axios from 'axios';

const GRID_SIZE = 100;
const CELL_SIZE = 20;
const MIN_SCALE = 0.3;
const MAX_SCALE = 3;
const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function GamePage() {
  const navigate = useNavigate();
  const [tonConnectUI] = useTonConnectUI();
  const wallet = useTonWallet();
  const [onlineCount, setOnlineCount] = useState(0);
  const stageRef = useRef(null);
  
  const [user, setUser] = useState(null);
  const [plots, setPlots] = useState([]);
  const [businessTypes, setBusinessTypes] = useState({});
  const [selectedPlot, setSelectedPlot] = useState(null);
  const [selectedPlotDetails, setSelectedPlotDetails] = useState(null);
  
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);
  const [showBuildModal, setShowBuildModal] = useState(false);
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [receiverAddress, setReceiverAddress] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [viewportSize, setViewportSize] = useState({ width: 800, height: 600 });

  // Calculate visible cells for virtualization
  const getVisibleCells = useCallback(() => {
    const mapWidth = viewportSize.width - 320; // Subtract right panel width
    const cellPixelSize = CELL_SIZE * scale;
    
    // Calculate viewport bounds in grid coordinates
    const startX = Math.max(0, Math.floor(-position.x / cellPixelSize));
    const startY = Math.max(0, Math.floor(-position.y / cellPixelSize));
    const endX = Math.min(GRID_SIZE, Math.ceil((mapWidth - position.x) / cellPixelSize) + 1);
    const endY = Math.min(GRID_SIZE, Math.ceil((viewportSize.height - position.y) / cellPixelSize) + 1);
    
    return { startX, startY, endX, endY };
  }, [position, scale, viewportSize]);

  // Load initial data
  useEffect(() => {
    if (!wallet?.account) {
      navigate('/');
      return;
    }
    loadData();
  }, [wallet]);

  // Handle viewport resize
  useEffect(() => {
    const handleResize = () => {
      const container = document.getElementById('map-container');
      if (container) {
        setViewportSize({
          width: container.clientWidth,
          height: container.clientHeight,
        });
      }
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch online count and send heartbeat
  useEffect(() => {
    const fetchOnline = async () => {
      try {
        const response = await axios.get(`${API_URL}/stats/online`);
        setOnlineCount(response.data.online_count || 0);
      } catch (e) {
        console.log('Could not fetch online count');
      }
    };
    
    const sendHeartbeat = async () => {
      const token = localStorage.getItem('ton_city_token');
      if (token) {
        try {
          await axios.post(`${API_URL}/stats/heartbeat`, {}, {
            headers: { Authorization: `Bearer ${token}` }
          });
        } catch (e) {}
      }
    };
    
    fetchOnline();
    sendHeartbeat();
    
    const interval = setInterval(() => {
      fetchOnline();
      sendHeartbeat();
    }, 60000); // every minute
    
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [plotsData, typesData, userData] = await Promise.all([
        getAllPlots(),
        getBusinessTypes(),
        getCurrentUser().catch(() => null),
      ]);
      
      setPlots(plotsData.plots || []);
      setBusinessTypes(typesData.business_types || {});
      setUser(userData);
      
      // Загрузить адрес получателя для пополнения
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/wallet-settings/public`);
        if (response.ok) {
          const settings = await response.json();
          setReceiverAddress(settings.receiver_address || '');
        }
      } catch (err) {
        console.log('Could not load wallet settings');
      }
      
      // Center view on the center of the map (50, 50)
      const centerX = 50;
      const centerY = 50;
      setPosition({
        x: viewportSize.width / 2 - (centerX * CELL_SIZE * scale),
        y: viewportSize.height / 2 - (centerY * CELL_SIZE * scale),
      });
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCellClick = async (x, y) => {
    setSelectedPlot({ x, y });
    try {
      const details = await getPlotByCoords(x, y);
      setSelectedPlotDetails(details);
    } catch (error) {
      console.error('Failed to get plot details:', error);
    }
  };

  const handlePurchase = async () => {
    if (!selectedPlotDetails || !wallet?.account) return;
    
    // Проверка баланса
    const plotPrice = selectedPlotDetails.price || 1;
    if (!user || user.balance_game < plotPrice) {
      toast.error(
        `Недостаточно средств! Нужно ${plotPrice.toFixed(2)} TON, у вас ${(user?.balance_game || 0).toFixed(2)} TON`,
        {
          action: {
            label: 'Пополнить',
            onClick: () => setShowDepositModal(true)
          }
        }
      );
      return;
    }
    
    setIsPurchasing(true);
    try {
      // Покупка с внутреннего баланса
      const purchaseData = await purchasePlot(selectedPlot.x, selectedPlot.y);
      
      toast.success(`Участок (${selectedPlot.x}, ${selectedPlot.y}) куплен!`);
      setShowPurchaseModal(false);
      setSelectedPlotDetails(null);
      loadData();
    } catch (error) {
      console.error('Purchase failed:', error);
      toast.error(error.response?.data?.detail || 'Ошибка покупки');
    } finally {
      setIsPurchasing(false);
    }
  };

  const handleBuild = async (businessType) => {
    if (!selectedPlotDetails || !wallet?.account) return;
    
    // Проверка баланса
    const businessPrice = businessTypes[businessType]?.cost || 10;
    if (!user || user.balance_game < businessPrice) {
      toast.error(
        `Недостаточно средств! Нужно ${businessPrice.toFixed(2)} TON, у вас ${(user?.balance_game || 0).toFixed(2)} TON`,
        {
          action: {
            label: 'Пополнить',
            onClick: () => setShowDepositModal(true)
          }
        }
      );
      return;
    }
    
    setIsBuilding(true);
    try {
      // Строительство с внутреннего баланса
      const buildData = await buildBusiness(selectedPlotDetails.id, businessType);
      
      toast.success(`${businessTypes[businessType]?.name || 'Бизнес'} построен!`);
      setShowBuildModal(false);
      setSelectedPlotDetails(null);
      loadData();
    } catch (error) {
      console.error('Build failed:', error);
      toast.error(error.response?.data?.detail || 'Ошибка строительства');
    } finally {
      setIsBuilding(false);
    }
  };

  const handleWheel = useCallback((e) => {
    e.evt.preventDefault();
    const scaleBy = 1.1;
    const stage = stageRef.current;
    const oldScale = scale;
    
    const pointer = stage.getPointerPosition();
    const mousePointTo = {
      x: (pointer.x - position.x) / oldScale,
      y: (pointer.y - position.y) / oldScale,
    };
    
    const newScale = e.evt.deltaY < 0 
      ? Math.min(oldScale * scaleBy, MAX_SCALE)
      : Math.max(oldScale / scaleBy, MIN_SCALE);
    
    setScale(newScale);
    setPosition({
      x: pointer.x - mousePointTo.x * newScale,
      y: pointer.y - mousePointTo.y * newScale,
    });
  }, [scale, position]);

  const handleDragStart = () => setIsDragging(true);
  const handleDragEnd = (e) => {
    setIsDragging(false);
    setPosition({
      x: e.target.x(),
      y: e.target.y(),
    });
  };

  const centerView = () => {
    setScale(1);
    const centerX = 50;
    const centerY = 50;
    setPosition({
      x: viewportSize.width / 2 - (centerX * CELL_SIZE),
      y: viewportSize.height / 2 - (centerY * CELL_SIZE),
    });
  };

  const zoomIn = () => setScale(Math.min(scale * 1.2, MAX_SCALE));
  const zoomOut = () => setScale(Math.max(scale / 1.2, MIN_SCALE));

  // Calculate plot price based on distance from center
  const calculatePrice = (x, y) => {
    const centerX = 50, centerY = 50;
    const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
    const maxDistance = Math.sqrt(50 * 50 + 50 * 50);
    return (10 + 90 * (1 - distance / maxDistance)).toFixed(2);
  };

  // Get cell color based on ownership
  const getCellColor = (x, y) => {
    const plot = plots.find(p => p.x === x && p.y === y);
    if (!plot || plot.is_available) {
      // Color based on distance from center (price indicator)
      const price = calculatePrice(x, y);
      const intensity = (price - 10) / 90;
      return `rgba(112, 0, 255, ${0.1 + intensity * 0.2})`;
    }
    if (plot.owner === wallet?.account?.address) {
      return plot.business_id ? 'rgba(255, 214, 0, 0.4)' : 'rgba(0, 240, 255, 0.4)';
    }
    return plot.business_id ? 'rgba(255, 214, 0, 0.2)' : 'rgba(0, 240, 255, 0.2)';
  };

  const getCellStroke = (x, y) => {
    const plot = plots.find(p => p.x === x && p.y === y);
    if (selectedPlot?.x === x && selectedPlot?.y === y) return '#00F0FF';
    if (plot?.business_id) return '#FFD600';
    return '#1F1F22';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-cyber-cyan animate-spin mx-auto mb-4" />
          <p className="text-text-muted font-rajdhani">Загрузка карты...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-void flex flex-col">
      {/* Header */}
      <header className="glass-panel border-b border-grid-border px-4 py-3 flex items-center justify-between z-20">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => navigate('/')}
            className="text-text-muted hover:text-text-main"
            data-testid="back-to-home-btn"
          >
            <Home className="w-4 h-4 mr-2" />
            Главная
          </Button>
          <div className="h-6 w-px bg-grid-border" />
          <h1 className="font-unbounded text-lg font-bold text-text-main flex items-center gap-3">
            TON City
            {/* Online users count */}
            <span className="flex items-center gap-1.5 px-2 py-1 bg-success/10 border border-success/30 rounded-lg text-sm font-normal">
              <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
              <Users className="w-3.5 h-3.5 text-success" />
              <span className="text-success font-mono">{onlineCount}</span>
            </span>
          </h1>
        </div>

        <div className="flex items-center gap-2 md:gap-4">
          {user && (
            <>
              {/* Баланс - адаптивный */}
              <div className="flex items-center gap-2 md:gap-3 px-3 md:px-4 py-2 bg-gradient-to-r from-green-500/10 to-green-600/10 border border-green-500/30 rounded-lg">
                <Wallet className="w-4 h-4 md:w-5 md:h-5 text-green-400" />
                <div>
                  <div className="text-xs text-gray-400 hidden md:block">Баланс</div>
                  <div className="text-base md:text-lg font-bold text-green-400 font-mono">
                    {user.balance_game?.toFixed(2) || '0.00'} TON
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <Button
                    size="sm"
                    onClick={() => setShowDepositModal(true)}
                    className="h-6 md:h-7 px-1.5 md:px-2 bg-green-600 hover:bg-green-700 text-xs"
                    data-testid="deposit-btn"
                    title="Пополнить"
                  >
                    <ArrowDownToLine className="w-3 h-3 md:mr-1" />
                    <span className="hidden sm:inline">Пополнить</span>
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowWithdrawModal(true)}
                    className="h-6 md:h-7 px-1.5 md:px-2 border-orange-500/30 text-orange-400 hover:bg-orange-500/10 text-xs"
                    data-testid="withdraw-btn"
                    title="Вывести"
                  >
                    <ArrowUpFromLine className="w-3 h-3 md:mr-1" />
                    <span className="hidden sm:inline">Вывести</span>
                  </Button>
                </div>
              </div>
              
              <div className="h-10 w-px bg-grid-border hidden lg:block" />
              
              {/* Статистика - скрыта на мобильных */}
              <div className="hidden lg:flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-cyber-cyan" />
                  <span className="text-text-muted">Участков:</span>
                  <span className="font-mono text-cyber-cyan">{user.plots_owned?.length || 0}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-signal-amber" />
                  <span className="text-text-muted">Бизнесов:</span>
                  <span className="font-mono text-signal-amber">{user.businesses_owned?.length || 0}</span>
                </div>
              </div>
            </>
          )}
          
          <Button 
            variant="outline"
            size="sm"
            onClick={() => navigate('/trading')}
            className="border-neon-purple/30 text-neon-purple hover:bg-neon-purple/10 hidden md:flex"
            data-testid="trading-btn"
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            Торговля
          </Button>
          
          <Button 
            variant="outline"
            size="sm"
            onClick={() => navigate('/dashboard')}
            className="border-cyber-cyan/30 text-cyber-cyan hover:bg-cyber-cyan/10"
            data-testid="dashboard-btn"
          >
            <Wallet className="w-4 h-4 md:mr-2" />
            <span className="hidden sm:inline">Dashboard</span>
          </Button>
        </div>
      </header>

      {/* Main content - карта по центру, список справа */}
      <div className="flex-1 flex">
        {/* Map - по центру */}
        <div id="map-container" className="flex-1 relative overflow-hidden">
          <Stage
            ref={stageRef}
            width={viewportSize.width - 320}
            height={viewportSize.height}
            onWheel={handleWheel}
            draggable
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            x={position.x}
            y={position.y}
            scaleX={scale}
            scaleY={scale}
          >
            <Layer>
              {/* Grid cells */}
              {Array.from({ length: GRID_SIZE }, (_, y) =>
                Array.from({ length: GRID_SIZE }, (_, x) => {
                  const plot = plots.find(p => p.x === x && p.y === y);
                  return (
                    <Group key={`${x}-${y}`}>
                      <Rect
                        x={x * CELL_SIZE}
                        y={y * CELL_SIZE}
                        width={CELL_SIZE}
                        height={CELL_SIZE}
                        fill={getCellColor(x, y)}
                        stroke={getCellStroke(x, y)}
                        strokeWidth={selectedPlot?.x === x && selectedPlot?.y === y ? 2 : 0.5}
                        onClick={() => handleCellClick(x, y)}
                        onTap={() => handleCellClick(x, y)}
                      />
                      {plot?.business_icon && scale > 0.8 && (
                        <Text
                          x={x * CELL_SIZE + CELL_SIZE / 2}
                          y={y * CELL_SIZE + CELL_SIZE / 2}
                          text={plot.business_icon}
                          fontSize={12}
                          offsetX={6}
                          offsetY={6}
                        />
                      )}
                    </Group>
                  );
                })
              )}
              
              {/* Center marker */}
              <Rect
                x={50 * CELL_SIZE - 2}
                y={50 * CELL_SIZE - 2}
                width={4}
                height={4}
                fill="#FF0055"
              />
            </Layer>
          </Stage>

          {/* Zoom controls */}
          <div className="absolute bottom-4 left-4 flex flex-col gap-2">
            <Button
              size="icon"
              variant="secondary"
              onClick={zoomIn}
              className="glass-panel w-10 h-10"
              data-testid="zoom-in-btn"
            >
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button
              size="icon"
              variant="secondary"
              onClick={zoomOut}
              className="glass-panel w-10 h-10"
              data-testid="zoom-out-btn"
            >
              <ZoomOut className="w-4 h-4" />
            </Button>
            <Button
              size="icon"
              variant="secondary"
              onClick={centerView}
              className="glass-panel w-10 h-10"
              data-testid="center-view-btn"
            >
              <Home className="w-4 h-4" />
            </Button>
            <Button
              size="icon"
              variant="secondary"
              onClick={loadData}
              className="glass-panel w-10 h-10"
              data-testid="refresh-btn"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>

          {/* Scale indicator */}
          <div className="absolute bottom-4 right-4 glass-panel rounded-lg px-3 py-2 text-sm font-mono text-text-muted">
            {Math.round(scale * 100)}%
          </div>
          
          {/* Legend */}
          <div className="absolute top-4 left-4 glass-panel rounded-lg p-3 text-xs">
            <div className="font-bold mb-2 text-text-main">Зоны:</div>
            <div className="space-y-1">
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#4ECDC4]"></span> Центр (100 TON)</div>
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#45B7D1]"></span> Бизнес (50 TON)</div>
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#96CEB4]"></span> Жилая (25 TON)</div>
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#DDA0DD]"></span> Промышл. (15 TON)</div>
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#2A2A32]"></span> Окраина (10 TON)</div>
            </div>
          </div>
        </div>

        {/* Right Panel - Список участков */}
        <div className="w-80 glass-panel border-l border-grid-border flex flex-col">
          {/* Panel Header */}
          <div className="p-4 border-b border-grid-border">
            <h2 className="font-unbounded text-lg font-bold text-text-main mb-2">
              Доступные участки
            </h2>
            <p className="text-xs text-text-muted">
              Выберите участок для покупки
            </p>
          </div>
          
          {/* Available Plots List */}
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-2">
              {/* Сгруппируем по зонам */}
              {['center', 'business', 'residential', 'industrial', 'outskirts'].map(zone => {
                const zonePlots = plots
                  .filter(p => p.is_available && p.zone === zone)
                  .slice(0, 5); // Показываем до 5 участков на зону
                
                if (zonePlots.length === 0) return null;
                
                const zoneNames = {
                  center: { name: 'Центр', price: 100, color: 'text-[#4ECDC4]' },
                  business: { name: 'Бизнес', price: 50, color: 'text-[#45B7D1]' },
                  residential: { name: 'Жилая', price: 25, color: 'text-[#96CEB4]' },
                  industrial: { name: 'Промышл.', price: 15, color: 'text-[#DDA0DD]' },
                  outskirts: { name: 'Окраина', price: 10, color: 'text-text-muted' }
                };
                
                return (
                  <div key={zone} className="mb-4">
                    <div className={`text-sm font-bold mb-2 ${zoneNames[zone].color}`}>
                      {zoneNames[zone].name} — {zoneNames[zone].price} TON
                    </div>
                    <div className="space-y-1">
                      {zonePlots.map(plot => (
                        <button
                          key={plot.id}
                          onClick={() => handleCellClick(plot.x, plot.y)}
                          className={`w-full text-left p-2 rounded-lg transition-colors ${
                            selectedPlot?.x === plot.x && selectedPlot?.y === plot.y
                              ? 'bg-cyber-cyan/20 border border-cyber-cyan/50'
                              : 'bg-void hover:bg-grid-border/50'
                          }`}
                        >
                          <div className="flex justify-between items-center">
                            <span className="font-mono text-sm">
                              ({plot.x}, {plot.y})
                            </span>
                            <span className="text-signal-amber font-mono text-sm">
                              {plot.price} TON
                            </span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
          
          {/* Selected Plot Details */}
          {selectedPlotDetails && (
            <div className="border-t border-grid-border p-4 bg-void/50">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="text-xs text-text-muted">Выбран участок</div>
                  <div className="font-mono text-lg text-cyber-cyan">
                    ({selectedPlotDetails.x}, {selectedPlotDetails.y})
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-text-muted">Цена</div>
                  <div className="font-mono text-lg text-signal-amber">
                    {selectedPlotDetails.price} TON
                  </div>
                </div>
              </div>
              
              <div className="text-xs text-text-muted mb-3">
                Зона: <span className="text-text-main capitalize">{selectedPlotDetails.zone}</span>
              </div>
              
              {selectedPlotDetails.is_available ? (
                <Button
                  onClick={() => setShowPurchaseModal(true)}
                  className="w-full btn-cyber"
                  disabled={isPurchasing || !user || user.balance_game < selectedPlotDetails.price}
                  data-testid="buy-plot-btn"
                >
                  {isPurchasing ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <MapPin className="w-4 h-4 mr-2" />
                  )}
                  Купить за {selectedPlotDetails.price} TON
                </Button>
              ) : selectedPlotDetails.owner === wallet?.account?.address ? (
                selectedPlotDetails.business ? (
                  <div className="glass-panel rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{selectedPlotDetails.business_icon}</span>
                      <span className="font-bold text-text-main">{selectedPlotDetails.business_name}</span>
                    </div>
                    <div className="text-xs text-text-muted">
                      Уровень {selectedPlotDetails.business?.level || 1}
                    </div>
                  </div>
                ) : (
                  <Button
                    onClick={() => setShowBuildModal(true)}
                    className="w-full bg-neon-purple hover:bg-neon-purple/80"
                    data-testid="build-btn"
                  >
                    <Building2 className="w-4 h-4 mr-2" />
                    Построить бизнес
                  </Button>
                )
              ) : (
                <div className="text-center text-text-muted text-sm py-2">
                  Этот участок уже куплен
                </div>
              )}
              
              {user && user.balance_game < (selectedPlotDetails.price || 0) && selectedPlotDetails.is_available && (
                <div className="mt-2 text-xs text-error text-center">
                  Недостаточно средств. 
                  <button 
                    onClick={() => setShowDepositModal(true)}
                    className="text-cyber-cyan underline ml-1"
                  >
                    Пополнить
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Purchase Modal */}
      <Dialog open={showPurchaseModal} onOpenChange={setShowPurchaseModal}>
        <DialogContent className="glass-panel border-grid-border text-text-main">
          <DialogHeader>
            <DialogTitle className="font-unbounded">Покупка участка</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            <div className="text-center">
              <div className="font-mono text-4xl text-signal-amber mb-2">
                {selectedPlotDetails?.price} TON
              </div>
              <div className="text-text-muted">
                Координаты: ({selectedPlotDetails?.x}, {selectedPlotDetails?.y})
              </div>
            </div>

            <div className="glass-panel rounded-lg p-4 text-sm text-text-muted">
              После покупки вы сможете построить бизнес на этом участке и получать доход от взаимодействия с соседними бизнесами.
            </div>

            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setShowPurchaseModal(false)}
              >
                Отмена
              </Button>
              <Button
                className="flex-1 btn-cyber"
                onClick={handlePurchase}
                disabled={isPurchasing}
                data-testid="confirm-purchase-btn"
              >
                {isPurchasing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Покупка...
                  </>
                ) : (
                  'Подтвердить'
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Build Modal */}
      <Dialog open={showBuildModal} onOpenChange={setShowBuildModal}>
        <DialogContent className="glass-panel border-grid-border text-text-main max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-unbounded">Выберите бизнес</DialogTitle>
          </DialogHeader>
          
          <ScrollArea className="max-h-96">
            <div className="grid gap-3">
              {Object.entries(businessTypes).map(([key, type]) => (
                <button
                  key={key}
                  onClick={() => handleBuild(key)}
                  disabled={isBuilding}
                  className="glass-panel glass-panel-hover rounded-xl p-4 text-left flex items-center gap-4 transition-all hover:border-cyber-cyan/30"
                  data-testid={`build-${key}-btn`}
                >
                  <span className="text-4xl">{type.icon}</span>
                  <div className="flex-1">
                    <div className="font-unbounded font-bold text-text-main">
                      {type.name}
                    </div>
                    <div className="text-sm text-text-muted">
                      {type.requires 
                        ? `Требует: ${type.requires}` 
                        : 'Не требует ресурсов'}
                    </div>
                    <div className="text-sm text-text-muted">
                      Производит: {type.produces}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-xl text-signal-amber">
                      {type.cost} TON
                    </div>
                    <div className="text-xs text-success">
                      +{type.base_income} TON/день
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </ScrollArea>

          {isBuilding && (
            <div className="flex items-center justify-center gap-2 text-text-muted">
              <Loader2 className="w-4 h-4 animate-spin" />
              Строительство...
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      {/* Deposit Modal */}
      <DepositModal
        isOpen={showDepositModal}
        onClose={() => setShowDepositModal(false)}
        onSuccess={loadData}
        receiverAddress={receiverAddress}
      />
      
      {/* Withdraw Modal */}
      <WithdrawModal
        isOpen={showWithdrawModal}
        onClose={() => setShowWithdrawModal(false)}
        onSuccess={loadData}
        currentBalance={user?.balance_game || 0}
        userWallet={wallet?.account?.address}
      />
    </div>
  );
}
