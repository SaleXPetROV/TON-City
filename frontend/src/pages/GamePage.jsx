import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Application, Container, Graphics, Text as PixiText, Sprite, Assets } from 'pixi.js';
import { 
  MapPin, Building2, Wallet, X, ArrowLeft,
  ZoomIn, ZoomOut, RefreshCw, Loader2, TrendingUp, 
  ArrowDownToLine, ArrowUpFromLine, Users, Coins,
  Info, ShoppingCart, Hammer, Check
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { DepositModal, WithdrawModal } from '@/components/BalanceModals';
import { useTranslation } from '@/lib/translations';
import { BUILDING_SPRITES, BUSINESS_CONFIG } from '@/lib/buildingSprites';
import { toast } from 'sonner';

// Isometric helpers
const TILE_WIDTH = 64;
const TILE_HEIGHT = 32;
const BUILDING_SIZE = 56;

function cartToIso(x, y) {
  return {
    x: (x - y) * (TILE_WIDTH / 2),
    y: (x + y) * (TILE_HEIGHT / 2)
  };
}

// Style colors
const STYLE_COLORS = {
  cyber: { land: 0x00f0ff, landDark: 0x0088aa, water: 0x001a33, owned: 0x00ff88, ownedDark: 0x00aa55 },
  tropical: { land: 0x4ade80, landDark: 0x22c55e, water: 0x0a2f1f, owned: 0x60e0ff, ownedDark: 0x40a0cc },
  industrial: { land: 0xf59e0b, landDark: 0xd97706, water: 0x1a1000, owned: 0x00ffcc, ownedDark: 0x00aa88 },
  neon: { land: 0xa855f7, landDark: 0x7c3aed, water: 0x0f001a, owned: 0x00ffaa, ownedDark: 0x00aa77 }
};

export default function GamePage({ user }) {
  const navigate = useNavigate();
  const { cityId } = useParams();
  const [tonConnectUI] = useTonConnectUI();
  const wallet = useTonWallet();
  
  const canvasRef = useRef(null);
  const appRef = useRef(null);
  const containerRef = useRef(null);
  const spritesLoadedRef = useRef(false);
  const loadedTexturesRef = useRef({});
  
  const [city, setCity] = useState(null);
  const [plots, setPlots] = useState([]);
  const [selectedPlot, setSelectedPlot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scale, setScale] = useState(1);
  
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);
  const [showBuildModal, setShowBuildModal] = useState(false);
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  const [selectedBusinessType, setSelectedBusinessType] = useState(null);
  const [userBalance, setUserBalance] = useState(user?.balance_ton || 0);
  
  const lang = localStorage.getItem('ton_city_lang') || 'en';
  const { t } = useTranslation(lang);

  // Load city data
  useEffect(() => {
    if (cityId) {
      loadCityData();
    } else {
      navigate('/map');
    }
  }, [cityId]);

  const loadCityData = async () => {
    try {
      setLoading(true);
      
      const res = await fetch(`/api/cities/${cityId}/plots`);
      if (!res.ok) throw new Error('City not found');
      
      const data = await res.json();
      setCity(data.city);
      setPlots(data.plots || []);
      
      const token = localStorage.getItem('token');
      if (token) {
        const userRes = await fetch('/api/auth/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (userRes.ok) {
          const userData = await userRes.json();
          setUserBalance(userData.balance_ton || 0);
        }
      }
    } catch (error) {
      console.error('Failed to load city:', error);
      toast.error(t('cityNotFound') || 'City not found');
      navigate('/map');
    } finally {
      setLoading(false);
    }
  };

  // Preload building sprites
  const preloadSprites = async () => {
    if (spritesLoadedRef.current) return loadedTexturesRef.current;
    
    const textures = {};
    for (const [type, config] of Object.entries(BUILDING_SPRITES)) {
      try {
        textures[type] = await Assets.load(config.url);
      } catch (e) {
        console.warn(`Failed to load sprite for ${type}:`, e);
      }
    }
    
    loadedTexturesRef.current = textures;
    spritesLoadedRef.current = true;
    return textures;
  };

  // Initialize PixiJS
  useEffect(() => {
    if (!canvasRef.current || loading || !city) return;
    
    const initPixi = async () => {
      if (appRef.current) {
        appRef.current.destroy(true);
      }
      
      const textures = await preloadSprites();
      
      const app = new Application();
      await app.init({
        width: canvasRef.current.clientWidth,
        height: canvasRef.current.clientHeight,
        backgroundColor: STYLE_COLORS[city.style]?.water || 0x001a33,
        antialias: true,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true
      });
      
      canvasRef.current.innerHTML = '';
      canvasRef.current.appendChild(app.canvas);
      appRef.current = app;
      
      const container = new Container();
      container.eventMode = 'static';
      app.stage.addChild(container);
      containerRef.current = container;
      
      drawCity(container, city.style, textures);
      centerView(app.screen.width, app.screen.height);
      
      // Pan & zoom
      let dragging = false;
      let lastPos = { x: 0, y: 0 };
      
      app.canvas.addEventListener('mousedown', (e) => {
        dragging = true;
        lastPos = { x: e.clientX, y: e.clientY };
      });
      
      app.canvas.addEventListener('mousemove', (e) => {
        if (dragging && containerRef.current) {
          const dx = e.clientX - lastPos.x;
          const dy = e.clientY - lastPos.y;
          containerRef.current.position.x += dx;
          containerRef.current.position.y += dy;
          lastPos = { x: e.clientX, y: e.clientY };
        }
      });
      
      app.canvas.addEventListener('mouseup', () => { dragging = false; });
      app.canvas.addEventListener('mouseleave', () => { dragging = false; });
      
      app.canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        handleZoom(delta);
      });
      
      const handleResize = () => {
        if (appRef.current && canvasRef.current) {
          appRef.current.renderer.resize(
            canvasRef.current.clientWidth,
            canvasRef.current.clientHeight
          );
        }
      };
      
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    };
    
    initPixi();
    
    return () => {
      if (appRef.current) {
        appRef.current.destroy(true);
        appRef.current = null;
      }
    };
  }, [loading, city, plots]);

  const drawCity = (container, style, textures) => {
    container.removeChildren();
    
    const colors = STYLE_COLORS[style] || STYLE_COLORS.cyber;
    const userId = user?.id;
    
    // Sort for isometric rendering
    const sortedPlots = [...plots].sort((a, b) => (a.x + a.y) - (b.x + b.y));
    
    sortedPlots.forEach(plot => {
      const { x: isoX, y: isoY } = cartToIso(plot.x, plot.y);
      const isOwned = plot.owner === userId;
      const hasBusiness = !!plot.business_type;
      
      // Draw tile
      const tile = new Graphics();
      let fillColor = colors.land;
      
      if (isOwned) {
        fillColor = colors.owned;
      } else if (plot.owner) {
        fillColor = 0x666666; // Other players' plots
      }
      
      tile.fill({ color: fillColor, alpha: 0.9 });
      tile.moveTo(TILE_WIDTH / 2, 0);
      tile.lineTo(TILE_WIDTH, TILE_HEIGHT / 2);
      tile.lineTo(TILE_WIDTH / 2, TILE_HEIGHT);
      tile.lineTo(0, TILE_HEIGHT / 2);
      tile.closePath();
      tile.fill();
      
      // Border
      const borderColor = isOwned ? colors.ownedDark : colors.landDark;
      tile.stroke({ width: 1, color: borderColor, alpha: 0.6 });
      tile.moveTo(TILE_WIDTH / 2, 0);
      tile.lineTo(TILE_WIDTH, TILE_HEIGHT / 2);
      tile.lineTo(TILE_WIDTH / 2, TILE_HEIGHT);
      tile.lineTo(0, TILE_HEIGHT / 2);
      tile.closePath();
      tile.stroke();
      
      tile.position.set(isoX, isoY);
      tile.eventMode = 'static';
      tile.cursor = 'pointer';
      
      tile.on('pointerdown', () => {
        setSelectedPlot(plot);
        if (!plot.owner) {
          setShowPurchaseModal(true);
        } else if (isOwned && !hasBusiness) {
          setShowBuildModal(true);
        }
      });
      
      tile.on('pointerover', () => { tile.alpha = 0.7; });
      tile.on('pointerout', () => { tile.alpha = 1; });
      
      container.addChild(tile);
      
      // Draw building sprite if exists
      if (hasBusiness && textures[plot.business_type]) {
        const sprite = new Sprite(textures[plot.business_type]);
        sprite.width = BUILDING_SIZE;
        sprite.height = BUILDING_SIZE;
        sprite.position.set(
          isoX + (TILE_WIDTH - BUILDING_SIZE) / 2,
          isoY - BUILDING_SIZE + TILE_HEIGHT
        );
        sprite.eventMode = 'static';
        sprite.cursor = 'pointer';
        sprite.on('pointerdown', () => setSelectedPlot(plot));
        container.addChild(sprite);
      }
    });
  };

  const centerView = (screenWidth, screenHeight) => {
    if (!containerRef.current || plots.length === 0) return;
    
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    plots.forEach(p => {
      const { x: isoX, y: isoY } = cartToIso(p.x, p.y);
      minX = Math.min(minX, isoX);
      minY = Math.min(minY, isoY);
      maxX = Math.max(maxX, isoX + TILE_WIDTH);
      maxY = Math.max(maxY, isoY + TILE_HEIGHT);
    });
    
    const cityWidth = maxX - minX;
    const cityHeight = maxY - minY;
    
    const scaleX = (screenWidth - 100) / cityWidth;
    const scaleY = (screenHeight - 100) / cityHeight;
    const newScale = Math.min(scaleX, scaleY, 1.5);
    
    containerRef.current.scale.set(newScale);
    containerRef.current.position.set(
      (screenWidth - cityWidth * newScale) / 2 - minX * newScale,
      (screenHeight - cityHeight * newScale) / 2 - minY * newScale
    );
    
    setScale(newScale);
  };

  const handleZoom = (delta) => {
    if (!containerRef.current) return;
    const newScale = Math.max(0.3, Math.min(2.5, scale + delta));
    containerRef.current.scale.set(newScale);
    setScale(newScale);
  };

  const handlePurchase = async () => {
    if (!selectedPlot || !user) return;
    
    setIsPurchasing(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/cities/${cityId}/plots/${selectedPlot.x}/${selectedPlot.y}/buy`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Purchase failed');
      
      toast.success(t('plotPurchased') || 'Plot purchased!');
      setShowPurchaseModal(false);
      setSelectedPlot(null);
      setUserBalance(data.new_balance);
      loadCityData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsPurchasing(false);
    }
  };

  const handleBuild = async () => {
    if (!selectedPlot || !selectedBusinessType || !user) return;
    
    setIsBuilding(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/cities/${cityId}/plots/${selectedPlot.x}/${selectedPlot.y}/build`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_type: selectedBusinessType })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Build failed');
      
      toast.success(t('businessBuilt') || 'Business built!');
      setShowBuildModal(false);
      setSelectedPlot(null);
      setSelectedBusinessType(null);
      setUserBalance(data.new_balance);
      loadCityData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsBuilding(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center font-rajdhani">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-cyber-cyan animate-spin" />
          <p className="text-cyber-cyan animate-pulse">Загрузка города...</p>
        </div>
      </div>
    );
  }

  const isMyPlot = selectedPlot?.owner === user?.id;

  return (
    <div className="h-screen bg-void relative overflow-hidden font-rajdhani flex flex-col">
      {/* Header */}
      <header className="flex-shrink-0 bg-black/80 backdrop-blur-xl border-b border-white/5 px-4 py-3 z-20">
        <div className="flex items-center justify-between max-w-screen-2xl mx-auto">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate('/map')} className="text-white/60 hover:text-white">
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('map') || 'Map'}
            </Button>
            
            <div className="hidden sm:flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyber-cyan to-neon-purple flex items-center justify-center">
                <MapPin className="w-4 h-4 text-black" />
              </div>
              <div>
                <h1 className="font-unbounded text-sm font-bold text-white uppercase tracking-tight">
                  {city?.name?.[lang] || city?.name?.en || cityId}
                </h1>
                <p className="text-[10px] text-cyber-cyan uppercase tracking-widest">
                  {plots.length} {t('plots') || 'plots'}
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/5 px-3 py-2 rounded-lg border border-white/10">
              <Coins className="w-4 h-4 text-signal-amber" />
              <span className="text-white font-mono text-sm font-bold">{userBalance?.toFixed(2) || '0.00'}</span>
              <span className="text-text-muted text-xs">TON</span>
            </div>
            
            <Button size="sm" variant="ghost" onClick={() => setShowDepositModal(true)} className="text-green-400 hover:bg-green-400/10 gap-1">
              <ArrowDownToLine className="w-4 h-4" />
              <span className="hidden sm:inline text-xs">Пополнить</span>
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setShowWithdrawModal(true)} className="text-red-400 hover:bg-red-400/10 gap-1">
              <ArrowUpFromLine className="w-4 h-4" />
              <span className="hidden sm:inline text-xs">Вывести</span>
            </Button>
            
            {user && (
              <div onClick={() => navigate('/settings')} className="flex items-center gap-2 cursor-pointer hover:opacity-80">
                {user.avatar ? (
                  <img src={user.avatar} alt="" className="w-8 h-8 rounded-full border border-cyber-cyan" />
                ) : (
                  <div className="w-8 h-8 bg-gradient-to-br from-cyber-cyan to-neon-purple rounded-full flex items-center justify-center text-sm font-bold text-black">
                    {(user.username || 'U')[0].toUpperCase()}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Canvas */}
      <div className="flex-1 relative">
        <div ref={canvasRef} className="absolute inset-0" style={{ touchAction: 'none' }} />
        
        {/* Zoom Controls */}
        <div className="absolute bottom-20 lg:bottom-6 right-4 flex flex-col gap-2 z-10">
          <Button size="sm" variant="outline" onClick={() => handleZoom(0.2)} className="bg-black/60 border-white/10 text-white hover:bg-black/80">
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="outline" onClick={() => handleZoom(-0.2)} className="bg-black/60 border-white/10 text-white hover:bg-black/80">
            <ZoomOut className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="outline" onClick={loadCityData} className="bg-black/60 border-white/10 text-white hover:bg-black/80">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
        
        {/* Selected Plot Info */}
        <AnimatePresence>
          {selectedPlot && !showPurchaseModal && !showBuildModal && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="absolute bottom-20 lg:bottom-6 left-4 right-20 lg:right-auto lg:w-80 bg-black/80 backdrop-blur-xl rounded-xl border border-white/10 p-4 z-10"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-bold text-white text-sm uppercase tracking-wide">
                    {t('plot') || 'Plot'} ({selectedPlot.x}, {selectedPlot.y})
                  </h3>
                  <p className="text-xs text-text-muted">
                    {selectedPlot.business_type ? (
                      <span className="text-signal-amber flex items-center gap-1">
                        {BUILDING_SPRITES[selectedPlot.business_type]?.icon} 
                        {BUILDING_SPRITES[selectedPlot.business_type]?.name?.[lang] || selectedPlot.business_type}
                      </span>
                    ) : isMyPlot ? (
                      <span className="text-green-400">{t('yourPlot') || 'Your Plot'}</span>
                    ) : selectedPlot.owner ? (
                      <span className="text-gray-400">{t('owned') || 'Owned'}</span>
                    ) : (
                      <span className="text-cyber-cyan">{t('available') || 'Available'}</span>
                    )}
                  </p>
                </div>
                <Button size="sm" variant="ghost" onClick={() => setSelectedPlot(null)} className="text-white/60 hover:text-white -mr-2 -mt-2">
                  <X className="w-4 h-4" />
                </Button>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-signal-amber font-mono font-bold text-lg">
                    {selectedPlot.price?.toFixed(2)} TON
                  </span>
                </div>
                
                {!selectedPlot.owner && (
                  <Button size="sm" onClick={() => setShowPurchaseModal(true)} className="bg-cyber-cyan text-black hover:bg-cyber-cyan/80">
                    <ShoppingCart className="w-4 h-4 mr-2" />
                    {t('buy') || 'Buy'}
                  </Button>
                )}
                
                {isMyPlot && !selectedPlot.business_type && (
                  <Button size="sm" onClick={() => setShowBuildModal(true)} className="bg-neon-purple text-white hover:bg-neon-purple/80">
                    <Hammer className="w-4 h-4 mr-2" />
                    {t('build') || 'Build'}
                  </Button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Purchase Modal */}
      <Dialog open={showPurchaseModal} onOpenChange={setShowPurchaseModal}>
        <DialogContent className="bg-panel border-grid-border max-w-md">
          <DialogHeader>
            <DialogTitle className="font-unbounded text-white uppercase tracking-tight">
              {t('buyPlot') || 'Buy Plot'}
            </DialogTitle>
          </DialogHeader>
          
          {selectedPlot && (
            <div className="space-y-4">
              <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-text-muted text-sm">{t('coordinates') || 'Coordinates'}</span>
                  <span className="text-white font-mono">({selectedPlot.x}, {selectedPlot.y})</span>
                </div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-text-muted text-sm">{t('price') || 'Price'}</span>
                  <span className="text-signal-amber font-mono font-bold">{selectedPlot.price?.toFixed(2)} TON</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-text-muted text-sm">{t('yourBalance') || 'Your Balance'}</span>
                  <span className={`font-mono font-bold ${userBalance >= selectedPlot.price ? 'text-green-400' : 'text-red-400'}`}>
                    {userBalance?.toFixed(2)} TON
                  </span>
                </div>
              </div>
              
              {userBalance < selectedPlot.price && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-center">
                  <p className="text-red-400 text-sm">{t('insufficientBalance') || 'Insufficient balance'}</p>
                  <Button size="sm" variant="outline" onClick={() => { setShowPurchaseModal(false); setShowDepositModal(true); }}
                    className="mt-2 border-red-500/30 text-red-400 hover:bg-red-500/10">
                    {t('deposit') || 'Deposit TON'}
                  </Button>
                </div>
              )}
              
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setShowPurchaseModal(false)} className="flex-1 border-white/10">
                  {t('cancel') || 'Cancel'}
                </Button>
                <Button onClick={handlePurchase} disabled={isPurchasing || userBalance < selectedPlot.price} className="flex-1 bg-cyber-cyan text-black hover:bg-cyber-cyan/80">
                  {isPurchasing ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <ShoppingCart className="w-4 h-4 mr-2" />}
                  {t('confirmPurchase') || 'Confirm'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Build Modal */}
      <Dialog open={showBuildModal} onOpenChange={setShowBuildModal}>
        <DialogContent className="bg-panel border-grid-border max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-unbounded text-white uppercase tracking-tight flex items-center gap-2">
              <Hammer className="w-5 h-5 text-neon-purple" />
              {t('buildBusiness') || 'Build Business'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <p className="text-text-muted text-sm">
              {t('selectBusinessToBuild') || 'Select a business type to build on your plot'}
            </p>
            
            <div className="grid grid-cols-2 gap-3 max-h-[300px] overflow-y-auto pr-2">
              {Object.entries(BUILDING_SPRITES).map(([type, config]) => {
                const businessConfig = BUSINESS_CONFIG[type];
                const canAfford = userBalance >= businessConfig?.cost;
                const isSelected = selectedBusinessType === type;
                
                return (
                  <div
                    key={type}
                    onClick={() => canAfford && setSelectedBusinessType(type)}
                    className={`relative p-3 rounded-xl border cursor-pointer transition-all ${
                      isSelected 
                        ? 'border-neon-purple bg-neon-purple/20' 
                        : canAfford 
                          ? 'border-white/10 bg-white/5 hover:border-white/20' 
                          : 'border-white/5 bg-white/2 opacity-50 cursor-not-allowed'
                    }`}
                  >
                    {isSelected && (
                      <div className="absolute top-2 right-2 w-5 h-5 bg-neon-purple rounded-full flex items-center justify-center">
                        <Check className="w-3 h-3 text-white" />
                      </div>
                    )}
                    <div className="text-2xl mb-2">{config.icon}</div>
                    <div className="font-bold text-white text-sm">{config.name[lang] || config.name.en}</div>
                    <div className="text-signal-amber font-mono text-xs">{businessConfig?.cost} TON</div>
                    <div className="text-text-muted text-[10px] mt-1">
                      +{businessConfig?.baseIncome}/day
                    </div>
                  </div>
                );
              })}
            </div>
            
            {selectedBusinessType && (
              <div className="bg-neon-purple/10 border border-neon-purple/20 rounded-lg p-3">
                <div className="flex justify-between items-center">
                  <span className="text-white font-bold">
                    {BUILDING_SPRITES[selectedBusinessType]?.icon} {BUILDING_SPRITES[selectedBusinessType]?.name[lang]}
                  </span>
                  <span className="text-signal-amber font-mono font-bold">
                    {BUSINESS_CONFIG[selectedBusinessType]?.cost} TON
                  </span>
                </div>
              </div>
            )}
            
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => { setShowBuildModal(false); setSelectedBusinessType(null); }} className="flex-1 border-white/10">
                {t('cancel') || 'Cancel'}
              </Button>
              <Button onClick={handleBuild} disabled={isBuilding || !selectedBusinessType} className="flex-1 bg-neon-purple text-white hover:bg-neon-purple/80">
                {isBuilding ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Hammer className="w-4 h-4 mr-2" />}
                {t('build') || 'Build'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <DepositModal isOpen={showDepositModal} onClose={() => setShowDepositModal(false)} onSuccess={loadCityData} />
      <WithdrawModal isOpen={showWithdrawModal} onClose={() => setShowWithdrawModal(false)} currentBalance={userBalance || 0} onSuccess={loadCityData} />
    </div>
  );
}
