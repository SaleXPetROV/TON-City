import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ArrowDownToLine, ArrowUpFromLine, AlertCircle, Info, Clock, Zap, Building2, Lock } from 'lucide-react';
import { toast } from 'sonner';
import { useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import axios from 'axios';
import { toUserFriendlyAddress } from '@/lib/tonAddress';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const WITHDRAWAL_FEE_PERCENT = 3;
const INSTANT_FEE_PERCENT = 1; // Bank fee
const NETWORK_FEE_TON = 0.05;

export function DepositModal({ isOpen, onClose, onSuccess, receiverAddress }) {
  const [tonConnectUI] = useTonConnectUI();
  const [amount, setAmount] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeDepositTab, setActiveDepositTab] = useState('ton');
  const [promoCode, setPromoCode] = useState('');
  const [isActivatingPromo, setIsActivatingPromo] = useState(false);

  const handleDeposit = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Введите корректную сумму');
      return;
    }

    const targetAddress = receiverAddress || 'EQDefault...'; // Адрес получателя
    if (!targetAddress || targetAddress === 'EQDefault...') {
      toast.error('Адрес получателя не настроен. Обратитесь к администратору.');
      return;
    }

    setIsProcessing(true);
    try {
      const amountNano = Math.floor(parseFloat(amount) * 1e9);

      const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 600,
        messages: [
          {
            address: targetAddress,
            amount: amountNano.toString(),
          },
        ],
      };

      await tonConnectUI.sendTransaction(transaction);
      toast.success('Транзакция отправлена! Баланс будет пополнен автоматически через 30-60 секунд.');

      if (onSuccess) onSuccess();
      onClose();
      setAmount('');
    } catch (error) {
      console.error('Deposit failed:', error);
      if (error.message && error.message.includes('reject')) {
        toast.error('Транзакция отменена');
      } else {
        toast.error('Ошибка пополнения');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleActivatePromo = async () => {
    if (!promoCode.trim()) {
      toast.error('Введите промокод');
      return;
    }
    setIsActivatingPromo(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API}/promo/activate?code=${encodeURIComponent(promoCode.trim())}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ошибка');
      toast.success(`Промокод активирован! +${data.amount} TON`);
      setPromoCode('');
      if (onSuccess) onSuccess();
    } catch (e) { toast.error(e.message); }
    finally { setIsActivatingPromo(false); }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-void border-white/10 text-white max-w-md" data-testid="deposit-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <ArrowDownToLine className="w-5 h-5 text-green-500" />
            Пополнить баланс
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeDepositTab} onValueChange={setActiveDepositTab} className="mt-4">
          <TabsList className="w-full bg-white/5 border border-white/10">
            <TabsTrigger value="ton" className="flex-1 data-[state=active]:bg-green-500/20 data-[state=active]:text-green-400">
              TON Перевод
            </TabsTrigger>
            <TabsTrigger value="promo" className="flex-1 data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400" data-testid="promo-tab">
              Промокод
            </TabsTrigger>
          </TabsList>

          <TabsContent value="ton" className="space-y-4 mt-4">
          <Alert className="bg-blue-500/10 border-blue-500/30">
            <Info className="h-4 w-4 text-blue-400" />
            <AlertDescription className="text-sm text-blue-300">
              Средства поступят на внутренний баланс автоматически в течение 1 минуты после подтверждения транзакции.
            </AlertDescription>
          </Alert>

          <div>
            <Label>Сумма пополнения (TON)</Label>
            <Input
              type="number"
              step="0.01"
              min="0.1"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Например: 10"
              className="mt-2 text-lg [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              data-testid="deposit-amount-input"
            />
          </div>

          {amount && parseFloat(amount) > 0 && (
            <div className="p-4 bg-white/5 rounded-lg space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Вы отправляете:</span>
                <span className="font-bold text-white">{parseFloat(amount).toFixed(2)} TON</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Комиссия сети (~):</span>
                <span className="text-yellow-400">{NETWORK_FEE_TON} TON</span>
              </div>
              <div className="h-px bg-white/10 my-2"></div>
              <div className="flex justify-between text-base">
                <span className="text-gray-300">Будет зачислено:</span>
                <span className="font-bold text-green-400">{parseFloat(amount).toFixed(2)} TON</span>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1"
              disabled={isProcessing}
            >
              Отмена
            </Button>
            <Button
              onClick={handleDeposit}
              disabled={!amount || parseFloat(amount) <= 0 || isProcessing}
              className="flex-1 bg-green-600 hover:bg-green-700"
              data-testid="confirm-deposit-btn"
            >
              {isProcessing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Обработка...
                </>
              ) : (
                <>
                  <ArrowDownToLine className="w-4 h-4 mr-2" />
                  Пополнить
                </>
              )}
            </Button>
          </div>
          </TabsContent>

          <TabsContent value="promo" className="space-y-4 mt-4">
            <Alert className="bg-amber-500/10 border-amber-500/30">
              <Info className="h-4 w-4 text-amber-400" />
              <AlertDescription className="text-sm text-amber-300">
                Введите промокод для мгновенного пополнения баланса.
              </AlertDescription>
            </Alert>

            <div>
              <Label>Промокод</Label>
              <Input
                data-testid="promo-code-activate-input"
                type="text"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                placeholder="Введите промокод"
                className="mt-2 text-lg uppercase tracking-wider"
                onKeyDown={(e) => e.key === 'Enter' && handleActivatePromo()}
              />
            </div>

            <Button
              data-testid="activate-promo-btn"
              onClick={handleActivatePromo}
              disabled={!promoCode.trim() || isActivatingPromo}
              className="w-full bg-amber-500 hover:bg-amber-600 text-black"
            >
              {isActivatingPromo ? 'Активация...' : 'Активировать промокод'}
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

export function WithdrawModal({ isOpen, onClose, onSuccess, currentBalance, userWallet }) {
  const [amount, setAmount] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [userDisplayAddress, setUserDisplayAddress] = useState('');
  const [withdrawType, setWithdrawType] = useState('standard'); // 'standard' or 'instant'
  const [banks, setBanks] = useState([]);
  const [selectedBank, setSelectedBank] = useState(null);
  const [totalDebt, setTotalDebt] = useState(0);
  const [availableForWithdraw, setAvailableForWithdraw] = useState(currentBalance);
  
  // 2FA verification states
  const [requires2FA, setRequires2FA] = useState(false);
  const [show2FADialog, setShow2FADialog] = useState(false);
  const [totpCode, setTotpCode] = useState('');
  const [is2FAChecking, setIs2FAChecking] = useState(false);
  const [pendingWithdrawal, setPendingWithdrawal] = useState(null);

  useEffect(() => {
    if (isOpen) {
      const loadData = async () => {
        try {
          const token = localStorage.getItem('token') || localStorage.getItem('ton_city_token');
          const [userRes, banksRes, securityRes, creditsRes] = await Promise.all([
            axios.get(`${API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } }),
            axios.get(`${API}/banks`),
            axios.get(`${API}/security/status`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
            axios.get(`${API}/credit/my-loans`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: { loans: [] } }))
          ]);
          setUserDisplayAddress(userRes.data.wallet_address_display || userRes.data.wallet_address);
          setBanks(banksRes.data.banks || []);
          setRequires2FA(securityRes.data?.is_2fa_enabled || false);
          
          // Calculate total debt from active credits
          const activeCredits = (creditsRes.data.loans || []).filter(c => c.status === 'active' || c.status === 'overdue');
          const debt = activeCredits.reduce((sum, c) => sum + (c.remaining_amount || c.remaining || 0), 0);
          setTotalDebt(debt);
          setAvailableForWithdraw(Math.max(0, (userRes.data.balance_ton || currentBalance) - debt));
        } catch (error) {
          console.error('Failed to load data:', error);
          setUserDisplayAddress(toUserFriendlyAddress(userWallet) || userWallet);
          setAvailableForWithdraw(currentBalance);
        }
      };
      loadData();
    }
  }, [isOpen, userWallet, currentBalance]);
  
  // Handle 2FA verification for withdrawal
  const verify2FAAndWithdraw = async () => {
    if (!totpCode || totpCode.length < 6) {
      toast.error('Введите 6-значный код 2FA');
      return;
    }
    
    setIs2FAChecking(true);
    try {
      // Execute withdrawal with 2FA code directly
      await executeWithdrawal(pendingWithdrawal, totpCode);
      setShow2FADialog(false);
      setTotpCode('');
      setPendingWithdrawal(null);
    } catch (error) {
      console.error('2FA verification failed:', error);
      let errorMsg = 'Неверный код 2FA';
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMsg = error.response.data.detail;
        }
      }
      toast.error(errorMsg);
    } finally {
      setIs2FAChecking(false);
    }
  };
  
  const executeWithdrawal = async (withdrawalData, totpCodeValue = null) => {
    const token = localStorage.getItem('token') || localStorage.getItem('ton_city_token');
    
    if (withdrawalData.type === 'instant') {
      await axios.post(
        `${API}/withdraw/instant`,
        {
          amount: withdrawalData.amount,
          bank_id: withdrawalData.bankId,
          totp_code: totpCodeValue,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Мгновенный вывод обрабатывается! Средства поступят в течение нескольких минут.');
    } else {
      await axios.post(
        `${API}/withdraw`,
        {
          amount: withdrawalData.amount,
          to_address: userWallet,
          totp_code: totpCodeValue,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Запрос на вывод создан! В истории транзакций будет отображаться статус "В ожидании". Обработка в течение 24 часов.');
    }
    
    if (onSuccess) onSuccess();
    onClose();
    setAmount('');
    setSelectedBank(null);
  };

  const handleWithdraw = async () => {
    if (parseFloat(amount) < 1) {
      toast.error('Минимальная сумма вывода: 1 TON');
      return;
    }

    if (withdrawType === 'instant' && !selectedBank) {
      toast.error('Выберите банк для мгновенного вывода');
      return;
    }
    
    // Check if 2FA is enabled - required for withdrawal
    if (!requires2FA) {
      toast.error('Для вывода средств необходимо включить 2FA в настройках безопасности');
      return;
    }
    
    const withdrawalData = {
      type: withdrawType,
      amount: parseFloat(amount),
      bankId: selectedBank?.id,
    };
    
    // Show 2FA verification dialog
    setPendingWithdrawal(withdrawalData);
    setShow2FADialog(true);
  };
  
  const platformFee = amount ? (parseFloat(amount) * WITHDRAWAL_FEE_PERCENT) / 100 : 0;
  const bankFee = withdrawType === 'instant' && amount ? (parseFloat(amount) * INSTANT_FEE_PERCENT) / 100 : 0;
  const totalFees = platformFee + bankFee;
  const receivedAmount = amount ? parseFloat(amount) - totalFees : 0;

  const hasWallet = userWallet || userDisplayAddress;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-void border-white/10 text-white max-w-lg" data-testid="withdraw-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <ArrowUpFromLine className="w-5 h-5 text-orange-500" />
            Вывести средства
          </DialogTitle>
          <DialogDescription className="text-text-muted">
            Выберите способ вывода: стандартный (24ч) или мгновенный через банк
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {!hasWallet ? (
            <Alert className="bg-red-500/10 border-red-500/30">
              <AlertCircle className="h-4 w-4 text-red-400" />
              <AlertDescription className="text-sm text-red-300">
                ⚠️ Подключите кошелёк для вывода средств
              </AlertDescription>
            </Alert>
          ) : (
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
              <span className="text-text-muted">Доступно:</span>
              <span className="text-2xl font-bold text-green-400">{currentBalance.toFixed(2)} TON</span>
            </div>
          )}

          {hasWallet && (
            <>
              {/* Withdrawal Type Tabs */}
              <Tabs value={withdrawType} onValueChange={setWithdrawType} className="w-full">
                <TabsList className="grid w-full grid-cols-2 bg-white/5">
                  <TabsTrigger value="standard" className="data-[state=active]:bg-white/10">
                    <Clock className="w-4 h-4 mr-2" />
                    Стандартный
                  </TabsTrigger>
                  <TabsTrigger value="instant" className="data-[state=active]:bg-yellow-500/20">
                    <Zap className="w-4 h-4 mr-2" />
                    Мгновенный
                  </TabsTrigger>
                </TabsList>
                
                <TabsContent value="standard" className="mt-4">
                  <Alert className="bg-blue-500/10 border-blue-500/30">
                    <Clock className="h-4 w-4 text-blue-400" />
                    <AlertDescription className="text-sm text-blue-300">
                      Обработка до 24 часов. Комиссия платформы: {WITHDRAWAL_FEE_PERCENT}%
                    </AlertDescription>
                  </Alert>
                </TabsContent>
                
                <TabsContent value="instant" className="mt-4 space-y-3">
                  <Alert className="bg-yellow-500/10 border-yellow-500/30">
                    <Zap className="h-4 w-4 text-yellow-400" />
                    <AlertDescription className="text-sm text-yellow-300">
                      Мгновенный вывод через банк. Дополнительная комиссия: {INSTANT_FEE_PERCENT}%
                    </AlertDescription>
                  </Alert>
                  
                  {banks.length === 0 ? (
                    <div className="p-4 bg-white/5 rounded-lg text-center text-text-muted">
                      <Building2 className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>Нет доступных банков</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Label>Выберите банк:</Label>
                      {banks.map(bank => (
                        <div
                          key={bank.id}
                          onClick={() => setSelectedBank(bank)}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedBank?.id === bank.id
                              ? 'border-yellow-500 bg-yellow-500/10'
                              : 'border-white/10 hover:border-white/30 bg-white/5'
                          }`}
                        >
                          <div className="flex justify-between items-center">
                            <div>
                              <div className="text-white font-medium">🏦 Gram Bank</div>
                              <div className="text-xs text-text-muted">
                                Владелец: {bank.owner_username || 'Unknown'} • Ур. {bank.level}
                              </div>
                            </div>
                            <Badge variant="outline" className="border-yellow-500/30 text-yellow-400">
                              -{bank.fee_rate * 100}%
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>
              </Tabs>

              <div>
                <Label>Сумма вывода (TON)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="1"
                  max={availableForWithdraw}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="Минимум 1 TON"
                  className="bg-white/5 border-white/10 text-white"
                />
                <div className="flex justify-between mt-2 text-xs">
                  <span className="text-text-muted">Баланс: {currentBalance?.toFixed(2) || '0.00'} TON</span>
                  <span className="text-green-400 font-medium">Доступно: {availableForWithdraw?.toFixed(2) || '0.00'} TON</span>
                </div>
                {totalDebt > 0 && (
                  <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <div className="flex items-center gap-2 text-red-400 text-xs">
                      <AlertCircle className="w-4 h-4" />
                      <span>Кредит: {totalDebt.toFixed(2)} TON (недоступно для вывода)</span>
                    </div>
                  </div>
                )}
              </div>

              {amount && parseFloat(amount) > 0 && (
                <div className="p-4 bg-white/5 rounded-lg space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Сумма:</span>
                    <span className="font-bold text-white">{parseFloat(amount).toFixed(2)} TON</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Комиссия платформы ({WITHDRAWAL_FEE_PERCENT}%):</span>
                    <span className="text-red-400">-{platformFee.toFixed(2)} TON</span>
                  </div>
                  {withdrawType === 'instant' && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Комиссия банка ({INSTANT_FEE_PERCENT}%):</span>
                      <span className="text-yellow-400">-{bankFee.toFixed(2)} TON</span>
                    </div>
                  )}
                  <div className="h-px bg-white/10 my-2"></div>
                  <div className="flex justify-between text-base">
                    <span className="text-gray-300">Вы получите:</span>
                    <span className="font-bold text-green-400">
                      {receivedAmount > 0 ? receivedAmount.toFixed(2) : '0.00'} TON
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-2">
                    <span>На кошелёк:</span>
                    <span className="font-mono text-right break-all max-w-[200px] truncate">
                      {userDisplayAddress || userWallet}
                    </span>
                  </div>
                </div>
              )}
            </>
          )}

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1"
              disabled={isProcessing}
            >
              Отмена
            </Button>
            <Button
              onClick={handleWithdraw}
              disabled={
                !hasWallet ||
                !amount ||
                parseFloat(amount) <= 0 ||
                parseFloat(amount) > availableForWithdraw ||
                parseFloat(amount) < 1 ||
                (withdrawType === 'instant' && !selectedBank) ||
                isProcessing
              }
              className={`flex-1 ${withdrawType === 'instant' ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-orange-600 hover:bg-orange-700'}`}
              data-testid="confirm-withdraw-btn"
            >
              {isProcessing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Обработка...
                </>
              ) : (
                <>
                  {withdrawType === 'instant' ? <Zap className="w-4 h-4 mr-2" /> : <ArrowUpFromLine className="w-4 h-4 mr-2" />}
                  {withdrawType === 'instant' ? 'Мгновенный вывод' : 'Запросить вывод'}
                </>
              )}
            </Button>
          </div>
          
          {/* 2FA Badge */}
          {requires2FA ? (
            <div className="flex items-center justify-center gap-2 p-2 bg-green-500/10 rounded-lg border border-green-500/20">
              <Lock className="w-4 h-4 text-green-400" />
              <span className="text-xs text-green-300">2FA включен - для вывода потребуется код</span>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-2 p-2 bg-red-500/10 rounded-lg border border-red-500/20">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <span className="text-xs text-red-300">Для вывода необходимо включить 2FA в настройках безопасности</span>
            </div>
          )}
        </div>
      </DialogContent>
      
      {/* 2FA Verification Dialog */}
      <Dialog open={show2FADialog} onOpenChange={(open) => {
        if (!open) {
          setShow2FADialog(false);
          setTotpCode('');
          setPendingWithdrawal(null);
        }
      }}>
        <DialogContent className="bg-void border-white/10 text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <Lock className="w-5 h-5 text-purple-400" />
              Подтверждение 2FA
            </DialogTitle>
            <DialogDescription className="text-text-muted">
              Введите 6-значный код из приложения аутентификации
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="p-4 bg-purple-500/10 rounded-lg border border-purple-500/20">
              <div className="flex justify-between mb-1">
                <span className="text-text-muted">Сумма вывода:</span>
                <span className="text-white font-bold">{pendingWithdrawal?.amount?.toFixed(2)} TON</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Тип:</span>
                <span className="text-white">{pendingWithdrawal?.type === 'instant' ? 'Мгновенный' : 'Стандартный'}</span>
              </div>
            </div>
            
            <div>
              <Label className="text-text-muted">Код 2FA</Label>
              <Input
                type="text"
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ''))}
                placeholder="000000"
                autoFocus
                className="mt-2 text-center text-2xl tracking-[0.5em] font-mono bg-white/5 border-white/10"
              />
            </div>
            
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => {
                  setShow2FADialog(false);
                  setTotpCode('');
                  setPendingWithdrawal(null);
                }}
                className="flex-1"
              >
                Отмена
              </Button>
              <Button
                onClick={verify2FAAndWithdraw}
                disabled={totpCode.length !== 6 || is2FAChecking}
                className="flex-1 bg-purple-600 hover:bg-purple-700"
              >
                {is2FAChecking ? 'Проверка...' : 'Подтвердить вывод'}
              </Button>
            </div>
            
            <p className="text-text-muted text-xs text-center">
              Также можно использовать резервный код
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </Dialog>
  );
}
