import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Stage, Layer, Rect, Group, Text } from 'react-konva';
import { 
  MapPin, Building2, Wallet, X, ChevronLeft, ChevronRight,
  ZoomIn, ZoomOut, Home, RefreshCw, Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  getAllPlots, getPlotByCoords, purchasePlot, confirmPlotPurchase,
  getBusinessTypes, buildBusiness, confirmBusinessBuild, getCurrentUser,
  tonToNano
} from '@/lib/api';
import { toast } from 'sonner';

const GRID_SIZE = 100;
const CELL_SIZE = 20;
const MIN_SCALE = 0.3;
const MAX_SCALE = 3;

export default function GamePage() {
  const navigate = useNavigate();
  const [tonConnectUI] = useTonConnectUI();
  const wallet = useTonWallet();
  const stageRef = useRef(null);
  
  const [user, setUser] = useState(null);
  const [plots, setPlots] = useState([]);
  const [businessTypes, setBusinessTypes] = useState({});
  const [selectedPlot, setSelectedPlot] = useState(null);
  const [selectedPlotDetails, setSelectedPlotDetails] = useState(null);
  
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);
  const [showBuildModal, setShowBuildModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [viewportSize, setViewportSize] = useState({ width: 800, height: 600 });

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
      
      // Center view
      setPosition({
        x: viewportSize.width / 2 - (GRID_SIZE * CELL_SIZE * scale) / 2,
        y: viewportSize.height / 2 - (GRID_SIZE * CELL_SIZE * scale) / 2,
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
    
    setIsPurchasing(true);
    try {
      // Initiate purchase on backend
      const purchaseData = await purchasePlot(selectedPlot.x, selectedPlot.y);
      
      // Send transaction via TON Connect
      const result = await tonConnectUI.sendTransaction({
        validUntil: Math.floor(Date.now() / 1000) + 600,
        messages: [{
          address: purchaseData.recipient || 'UQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa',
          amount: tonToNano(purchaseData.amount_ton),
        }],
      });
      
      // Confirm on backend
      await confirmPlotPurchase(purchaseData.transaction_id, result.boc);
      
      toast.success(`Участок (${selectedPlot.x}, ${selectedPlot.y}) куплен!`);
      setShowPurchaseModal(false);
      setSelectedPlotDetails(null);
      loadData();
    } catch (error) {
      console.error('Purchase failed:', error);
      toast.error(error.message || 'Ошибка покупки');
    } finally {
      setIsPurchasing(false);
    }
  };

  const handleBuild = async (businessType) => {
    if (!selectedPlotDetails || !wallet?.account) return;
    
    setIsBuilding(true);
    try {
      // Initiate build on backend
      const buildData = await buildBusiness(selectedPlotDetails.id, businessType);
      
      // Send transaction via TON Connect
      const result = await tonConnectUI.sendTransaction({
        validUntil: Math.floor(Date.now() / 1000) + 600,
        messages: [{
          address: buildData.recipient || 'UQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa',
          amount: tonToNano(buildData.amount_ton),
        }],
      });
      
      // Confirm on backend
      await confirmBusinessBuild(buildData.transaction_id, result.boc);
      
      toast.success(`${businessTypes[businessType]?.name || 'Бизнес'} построен!`);
      setShowBuildModal(false);
      setSelectedPlotDetails(null);
      loadData();
    } catch (error) {
      console.error('Build failed:', error);
      toast.error(error.message || 'Ошибка строительства');
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
    setPosition({
      x: viewportSize.width / 2 - (GRID_SIZE * CELL_SIZE) / 2,
      y: viewportSize.height / 2 - (GRID_SIZE * CELL_SIZE) / 2,
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
          <h1 className="font-unbounded text-lg font-bold text-text-main">
            TON City
          </h1>
        </div>

        <div className="flex items-center gap-4">
          {user && (
            <div className="flex items-center gap-6 text-sm">
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
          )}
          
          <Button 
            variant="outline"
            size="sm"
            onClick={() => navigate('/dashboard')}
            className="border-cyber-cyan/30 text-cyber-cyan hover:bg-cyber-cyan/10"
            data-testid="dashboard-btn"
          >
            <Wallet className="w-4 h-4 mr-2" />
            Dashboard
          </Button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Map */}
        <div id="map-container" className="flex-1 relative overflow-hidden">
          <Stage
            ref={stageRef}
            width={viewportSize.width}
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
        </div>

        {/* Side panel */}
        <AnimatePresence>
          {selectedPlotDetails && (
            <motion.div
              initial={{ x: 300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 300, opacity: 0 }}
              className="w-80 glass-panel border-l border-grid-border p-6 overflow-auto"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-unbounded text-lg font-bold text-text-main">
                  Участок
                </h2>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => {
                    setSelectedPlot(null);
                    setSelectedPlotDetails(null);
                  }}
                  data-testid="close-panel-btn"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {/* Coordinates */}
              <div className="glass-panel rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <MapPin className="w-4 h-4 text-cyber-cyan" />
                  <span className="text-text-muted text-sm">Координаты</span>
                </div>
                <div className="font-mono text-2xl text-cyber-cyan">
                  ({selectedPlotDetails.x}, {selectedPlotDetails.y})
                </div>
              </div>

              {/* Price / Owner */}
              {selectedPlotDetails.is_available ? (
                <div className="glass-panel rounded-lg p-4 mb-4">
                  <div className="text-text-muted text-sm mb-2">Цена</div>
                  <div className="font-mono text-3xl text-signal-amber">
                    {selectedPlotDetails.price} TON
                  </div>
                </div>
              ) : (
                <div className="glass-panel rounded-lg p-4 mb-4">
                  <div className="text-text-muted text-sm mb-2">Владелец</div>
                  <div className="font-mono text-sm text-cyber-cyan truncate">
                    {selectedPlotDetails.owner === wallet?.account?.address 
                      ? 'Вы' 
                      : `${selectedPlotDetails.owner?.slice(0, 8)}...`}
                  </div>
                </div>
              )}

              {/* Business info */}
              {selectedPlotDetails.business && (
                <div className="glass-panel rounded-lg p-4 mb-4">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-3xl">{selectedPlotDetails.business_info?.icon}</span>
                    <div>
                      <div className="font-unbounded font-bold text-text-main">
                        {selectedPlotDetails.business_info?.name}
                      </div>
                      <div className="text-sm text-text-muted">
                        Уровень {selectedPlotDetails.business.level}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-text-muted">Доход</span>
                    <span className="font-mono text-success">
                      +{selectedPlotDetails.business.income_rate?.toFixed(2)} TON/день
                    </span>
                  </div>
                  {selectedPlotDetails.business.connected_businesses?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-grid-border">
                      <span className="text-text-muted text-sm">
                        Связей: {selectedPlotDetails.business.connected_businesses.length}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="space-y-3">
                {selectedPlotDetails.is_available && (
                  <Button
                    className="w-full btn-cyber"
                    onClick={() => setShowPurchaseModal(true)}
                    data-testid="buy-plot-btn"
                  >
                    Купить участок
                  </Button>
                )}

                {selectedPlotDetails.owner === wallet?.account?.address && 
                 !selectedPlotDetails.business_id && (
                  <Button
                    className="w-full btn-ton"
                    onClick={() => setShowBuildModal(true)}
                    data-testid="build-business-btn"
                  >
                    <Building2 className="w-4 h-4 mr-2" />
                    Построить бизнес
                  </Button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
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
    </div>
  );
}
