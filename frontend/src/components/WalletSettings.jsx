import { useState, useEffect } from 'react';
import { Wallet, Globe, AlertCircle, Save, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function WalletSettings({ token }) {
  const [settings, setSettings] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  
  // Form
  const [network, setNetwork] = useState('testnet');
  const [receiverAddress, setReceiverAddress] = useState('');
  
  useEffect(() => {
    loadData();
  }, []);
  
  const loadData = async () => {
    setIsLoading(true);
    try {
      const [settingsRes, depositsRes] = await Promise.all([
        axios.get(`${API}/admin/wallet-settings`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/deposits?limit=20`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      const s = settingsRes.data;
      setSettings(s);
      setNetwork(s.network || 'testnet');
      setReceiverAddress(s.receiver_address || '');
      
      setDeposits(depositsRes.data.deposits || []);
    } catch (error) {
      console.error('Failed to load wallet settings:', error);
      toast.error('Ошибка загрузки настроек');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSave = async () => {
    if (!receiverAddress) {
      toast.error('Введите адрес кошелька');
      return;
    }
    
    setIsSaving(true);
    try {
      await axios.post(
        `${API}/admin/wallet-settings`,
        { network, receiver_address: receiverAddress },
        { 
          headers: { Authorization: `Bearer ${token}` },
          params: { network, receiver_address: receiverAddress }
        }
      );
      
      toast.success('✅ Настройки сохранены!');
      loadData();
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Ошибка сохранения');
    } finally {
      setIsSaving(false);
    }
  };
  
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
      {/* Configuration */}
      <Card className="bg-white/5 border-white/10" data-testid="wallet-config-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="w-5 h-5 text-neon-blue" />
            Настройки TON кошелька
          </CardTitle>
          <CardDescription>
            Настройте адрес для получения TON платежей и выберите сеть
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Globe className="w-4 h-4" />
              Сеть
            </Label>
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
          </div>
          
          <div className="space-y-2">
            <Label>Адрес для получения платежей</Label>
            <Input
              value={receiverAddress}
              onChange={(e) => setReceiverAddress(e.target.value)}
              placeholder="EQxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              className="font-mono text-sm"
              data-testid="receiver-address-input"
            />
            <p className="text-xs text-gray-400">
              Все платежи будут приходить на этот адрес. После поступления средств, внутренний баланс игрока пополнится автоматически.
            </p>
          </div>
          
          <Button
            onClick={handleSave}
            disabled={isSaving || !receiverAddress}
            className="w-full"
            data-testid="save-settings-btn"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Сохранение...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Сохранить настройки
              </>
            )}
          </Button>
        </CardContent>
      </Card>
      
      {/* Current Settings Display */}
      {settings && (
        <Card className="bg-neon-blue/10 border-neon-blue/30">
          <CardHeader>
            <CardTitle className="text-lg">Текущие настройки</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-400">Сеть:</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant={settings.network === 'mainnet' ? 'default' : 'secondary'}>
                    {settings.network === 'mainnet' ? 'Mainnet' : 'Testnet'}
                  </Badge>
                  {settings.network === 'mainnet' && (
                    <span className="text-xs text-green-400">● Реальные деньги</span>
                  )}
                </div>
              </div>
              
              <div>
                <p className="text-sm text-gray-400">Адрес получателя:</p>
                <p className="font-mono text-sm mt-1 break-all">
                  {settings.receiver_address || 'Не настроен'}
                </p>
              </div>
              
              <div>
                <p className="text-sm text-gray-400">Последнее обновление:</p>
                <p className="text-sm mt-1">
                  {settings.updated_at ? new Date(settings.updated_at).toLocaleString('ru-RU') : 'Никогда'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Deposits History */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            История пополнений
          </CardTitle>
          <CardDescription>
            Последние 20 пополнений внутреннего баланса
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            {deposits.length > 0 ? (
              <div className="space-y-3">
                {deposits.map((deposit, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-white/5 rounded-lg border border-white/10"
                    data-testid={`deposit-${idx}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant={deposit.status === 'completed' ? 'default' : 'secondary'}>
                        {deposit.status === 'completed' ? 'Завершено' : 'Ожидание'}
                      </Badge>
                      <span className="text-lg font-bold text-neon-blue">
                        {deposit.amount_ton} TON
                      </span>
                    </div>
                    
                    <div className="space-y-1 text-sm">
                      <div>
                        <span className="text-gray-400">От: </span>
                        <span className="font-mono">{deposit.wallet_address?.slice(0, 12)}...</span>
                      </div>
                      
                      <div>
                        <span className="text-gray-400">TX: </span>
                        <span className="font-mono text-xs">{deposit.tx_hash?.slice(0, 20)}...</span>
                      </div>
                      
                      <div>
                        <span className="text-gray-400">Дата: </span>
                        <span>{new Date(deposit.created_at).toLocaleString('ru-RU')}</span>
                      </div>
                      
                      {deposit.memo && (
                        <div>
                          <span className="text-gray-400">Комментарий: </span>
                          <span>{deposit.memo}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Wallet className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">Пока нет пополнений</p>
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
