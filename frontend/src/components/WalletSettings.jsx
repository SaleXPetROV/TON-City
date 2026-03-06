import { useState, useEffect } from 'react';
import { Wallet, Globe, AlertCircle, Save, Plus, Trash2, Percent } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function WalletSettings({ token }) {
  const [settings, setSettings] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  
  // Wallets with percentages
  const [wallets, setWallets] = useState([]);
  const [showAddWallet, setShowAddWallet] = useState(false);
  const [newWallet, setNewWallet] = useState({ address: '', percentage: 100, mnemonic: '' });
  
  // Form
  const [network, setNetwork] = useState('testnet');
  
  useEffect(() => {
    loadData();
  }, []);
  
  const loadData = async () => {
    setIsLoading(true);
    try {
      const [settingsRes, depositsRes, walletsRes] = await Promise.all([
        axios.get(`${API}/admin/wallet-settings`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/deposits?limit=20`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/wallets`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: { wallets: [] } }))
      ]);
      
      const s = settingsRes.data;
      setSettings(s);
      setNetwork(s.network || 'testnet');
      setDeposits(depositsRes.data.deposits || []);
      setWallets(walletsRes.data.wallets || []);
    } catch (error) {
      console.error('Failed to load wallet settings:', error);
      toast.error('Ошибка загрузки настроек');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSaveNetwork = async () => {
    setIsSaving(true);
    try {
      await axios.post(
        `${API}/admin/wallet-settings?network=${network}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Сеть сохранена!');
      loadData();
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Ошибка сохранения');
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleAddWallet = async () => {
    if (!newWallet.address) {
      toast.error('Введите адрес кошелька');
      return;
    }
    
    const totalPercentage = wallets.reduce((sum, w) => sum + w.percentage, 0) + newWallet.percentage;
    if (totalPercentage > 100) {
      toast.error(`Общий процент превысит 100%! Доступно: ${100 - wallets.reduce((sum, w) => sum + w.percentage, 0)}%`);
      return;
    }
    
    try {
      const res = await axios.post(
        `${API}/admin/wallets`,
        newWallet,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setWallets([...wallets, res.data.wallet]);
      setShowAddWallet(false);
      setNewWallet({ address: '', percentage: 100, mnemonic: '' });
      toast.success('Кошелёк добавлен!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка добавления');
    }
  };
  
  const handleDeleteWallet = async (walletId) => {
    try {
      await axios.delete(`${API}/admin/wallets/${walletId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setWallets(wallets.filter(w => w.id !== walletId));
      toast.success('Кошелёк удалён');
    } catch {
      toast.error('Ошибка удаления');
    }
  };
  
  const totalPercentage = wallets.reduce((sum, w) => sum + w.percentage, 0);
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neon-blue mx-auto"></div>
          <p className="mt-4 text-gray-400">Загрузка...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Network Configuration */}
      <Card className="bg-white/5 border-white/10" data-testid="wallet-config-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-neon-blue" />
            Настройки сети
          </CardTitle>
          <CardDescription>
            Выберите сеть TON для приёма платежей
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Select value={network} onValueChange={setNetwork}>
            <SelectTrigger data-testid="network-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="testnet">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">Test</Badge>
                  <span>Testnet (для тестирования)</span>
                </div>
              </SelectItem>
              <SelectItem value="mainnet">
                <div className="flex items-center gap-2">
                  <Badge variant="default" className="bg-green-500">Live</Badge>
                  <span>Mainnet (реальные деньги)</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
          
          {network === 'mainnet' && (
            <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <span className="text-sm text-red-400">
                Mainnet режим - будут использоваться реальные TON!
              </span>
            </div>
          )}
          
          {network === 'testnet' && (
            <div className="flex items-center gap-2 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <AlertCircle className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-blue-400">
                Testnet режим - используйте тестовые TON для проверки
              </span>
            </div>
          )}
          
          <Button
            onClick={handleSaveNetwork}
            disabled={isSaving}
            className="w-full"
          >
            {isSaving ? 'Сохранение...' : 'Сохранить сеть'}
          </Button>
        </CardContent>
      </Card>
      
      {/* Wallets for Deposits */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Wallet className="w-5 h-5 text-green-400" />
                Кошельки для пополнений
              </CardTitle>
              <CardDescription>
                Добавьте кошельки и укажите процент от суммы пополнений для каждого
              </CardDescription>
            </div>
            <Button
              onClick={() => setShowAddWallet(true)}
              className="bg-green-500 text-black hover:bg-green-600"
              disabled={totalPercentage >= 100}
            >
              <Plus className="w-4 h-4 mr-2" />
              Добавить
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Total percentage indicator */}
          <div className="mb-4 p-3 bg-white/5 rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <span className="text-text-muted text-sm">Общий процент распределения:</span>
              <span className={`font-bold ${totalPercentage === 100 ? 'text-green-400' : totalPercentage > 100 ? 'text-red-400' : 'text-amber-400'}`}>
                {totalPercentage}%
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all ${totalPercentage === 100 ? 'bg-green-500' : totalPercentage > 100 ? 'bg-red-500' : 'bg-amber-500'}`}
                style={{ width: `${Math.min(totalPercentage, 100)}%` }}
              />
            </div>
            {totalPercentage !== 100 && (
              <p className="text-xs text-amber-400 mt-2">
                {totalPercentage < 100 
                  ? `⚠️ Не распределено: ${100 - totalPercentage}% (средства не будут зачисляться полностью)` 
                  : '⚠️ Сумма процентов превышает 100%!'
                }
              </p>
            )}
          </div>
          
          {wallets.length === 0 ? (
            <div className="text-center py-8 text-text-muted">
              <Wallet className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p>Кошельки не добавлены</p>
              <p className="text-sm">При пополнении средства не будут распределяться</p>
            </div>
          ) : (
            <div className="space-y-3">
              {wallets.map((wallet, idx) => (
                <div 
                  key={wallet.id || idx}
                  className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10"
                >
                  <div className="flex-1">
                    <div className="font-mono text-sm text-white break-all">
                      {wallet.address}
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                        <Percent className="w-3 h-3 mr-1" />
                        {wallet.percentage}%
                      </Badge>
                      {wallet.mnemonic && (
                        <Badge variant="outline" className="border-purple-500/30 text-purple-400">
                          Автовывод
                        </Badge>
                      )}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDeleteWallet(wallet.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Recent Deposits */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader>
          <CardTitle className="text-lg">Последние пополнения</CardTitle>
        </CardHeader>
        <CardContent>
          {deposits.length === 0 ? (
            <p className="text-center text-gray-400 py-4">Пополнений пока нет</p>
          ) : (
            <ScrollArea className="h-[300px]">
              <div className="space-y-3">
                {deposits.map((deposit) => (
                  <div 
                    key={deposit.id}
                    className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10"
                  >
                    <div>
                      <div className="font-mono text-sm text-white">
                        {deposit.from_address?.slice(0, 10)}...{deposit.from_address?.slice(-8)}
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(deposit.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-green-400">+{deposit.amount} TON</div>
                      <Badge variant={deposit.status === 'completed' ? 'default' : 'secondary'}>
                        {deposit.status === 'completed' ? 'Зачислено' : deposit.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
      
      {/* Add Wallet Dialog */}
      <Dialog open={showAddWallet} onOpenChange={setShowAddWallet}>
        <DialogContent className="bg-void border-green-500/30">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Wallet className="w-5 h-5 text-green-400" />
              Добавить кошелёк
            </DialogTitle>
            <DialogDescription className="text-text-muted">
              Укажите адрес кошелька и процент от суммы пополнений
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-text-muted">Адрес кошелька</Label>
              <Input 
                value={newWallet.address}
                onChange={(e) => setNewWallet({...newWallet, address: e.target.value})}
                placeholder="EQ..."
                className="bg-white/5 border-white/10 font-mono"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-text-muted">Процент от пополнений (%)</Label>
              <Input 
                type="number"
                min="1"
                max={100 - totalPercentage}
                value={newWallet.percentage}
                onChange={(e) => setNewWallet({...newWallet, percentage: parseInt(e.target.value) || 0})}
                className="bg-white/5 border-white/10"
              />
              <p className="text-xs text-text-muted">
                Доступно для распределения: {100 - totalPercentage}%
              </p>
            </div>
            
            <div className="space-y-2">
              <Label className="text-text-muted">Мнемоническая фраза (опционально)</Label>
              <Input 
                type="password"
                value={newWallet.mnemonic}
                onChange={(e) => setNewWallet({...newWallet, mnemonic: e.target.value})}
                placeholder="24 слова через пробел..."
                className="bg-white/5 border-white/10"
              />
              <p className="text-xs text-amber-400">
                ⚠️ Если указать мнемонику, система сможет автоматически отправлять средства
              </p>
            </div>
          </div>
          
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowAddWallet(false)}
              className="border-white/10"
            >
              Отмена
            </Button>
            <Button 
              onClick={handleAddWallet}
              className="bg-green-500 text-black hover:bg-green-600"
            >
              Добавить кошелёк
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
