import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowDownToLine, ArrowUpFromLine, AlertCircle, Info } from 'lucide-react';
import { toast } from 'sonner';
import { useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import axios from 'axios';
import { toUserFriendlyAddress } from '@/lib/tonAddress';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const WITHDRAWAL_FEE_PERCENT = 3;
const NETWORK_FEE_TON = 0.05;

export function DepositModal({ isOpen, onClose, onSuccess, receiverAddress }) {
  const [tonConnectUI] = useTonConnectUI();
  const [amount, setAmount] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

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

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-void border-white/10 text-white max-w-md" data-testid="deposit-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <ArrowDownToLine className="w-5 h-5 text-green-500" />
            Пополнить баланс
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-4">
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
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function WithdrawModal({ isOpen, onClose, onSuccess, currentBalance, userWallet }) {
  const [amount, setAmount] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [userDisplayAddress, setUserDisplayAddress] = useState('');

  useEffect(() => {
    if (isOpen) {
      const loadUserAddress = async () => {
        try {
          const token = localStorage.getItem('ton_city_token');
          const response = await axios.get(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          // Используем адрес из БД (wallet_address_display), а не локально перекодируем
          setUserDisplayAddress(response.data.wallet_address_display || response.data.wallet_address);
        } catch (error) {
          console.error('Failed to load user address:', error);
          // Fallback на локальное преобразование, если API не ответил
          setUserDisplayAddress(toUserFriendlyAddress(userWallet) || userWallet);
        }
      };
      loadUserAddress();
    }
  }, [isOpen, userWallet]);
    if (parseFloat(amount) < 1) {
      toast.error('Минимальная сумма вывода: 1 TON');
      return;
    }

    setIsProcessing(true);
    try {
      const token = localStorage.getItem('ton_city_token');
      await axios.post(
        `${API}/withdraw`,
        {
          amount: parseFloat(amount),
          to_address: userWallet,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Запрос на вывод отправлен! Ожидайте подтверждения администратора.');
      if (onSuccess) onSuccess();
      onClose();
      setAmount('');
    } catch (error) {
      console.error('Withdrawal failed:', error);
      toast.error(error.response?.data?.detail || 'Ошибка создания запроса на вывод');
    } finally {
      setIsProcessing(false);
    }
  };
  
  const withdrawalFee = amount ? (parseFloat(amount) * WITHDRAWAL_FEE_PERCENT) / 100 : 0;
  const totalDeducted = amount ? parseFloat(amount) : 0;
  const receivedAmount = totalDeducted - withdrawalFee - NETWORK_FEE_TON;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-void border-white/10 text-white max-w-md" data-testid="withdraw-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <ArrowUpFromLine className="w-5 h-5 text-orange-500" />
            Вывести средства
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          <Alert className="bg-yellow-500/10 border-yellow-500/30">
            <AlertCircle className="h-4 w-4 text-yellow-400" />
            <AlertDescription className="text-sm text-yellow-300">
              Вывод средств требует подтверждения администратора. Обычно это занимает до 24 часов.
            </AlertDescription>
          </Alert>

          <div>
            <Label>Доступно для вывода</Label>
            <div className="text-2xl font-bold text-green-400 mt-1">
              {currentBalance.toFixed(2)} TON
            </div>
          </div>

          <div>
            <Label>Сумма вывода (TON)</Label>
            <Input
              type="number"
              step="0.01"
              min="1"
              max={currentBalance}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Минимум 1 TON"
              className="mt-2 text-lg [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              data-testid="withdraw-amount-input"
            />
          </div>

          {amount && parseFloat(amount) > 0 && (
            <div className="p-4 bg-white/5 rounded-lg space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Сумма запроса:</span>
                <span className="font-bold text-white">{parseFloat(amount).toFixed(2)} TON</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Комиссия вывода ({WITHDRAWAL_FEE_PERCENT}%):</span>
                <span className="text-red-400">-{withdrawalFee.toFixed(4)} TON</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Комиссия сети (~):</span>
                <span className="text-red-400">-{NETWORK_FEE_TON} TON</span>
              </div>
              <div className="h-px bg-white/10 my-2"></div>
              <div className="flex justify-between text-base">
                <span className="text-gray-300">Вы получите:</span>
                <span className="font-bold text-green-400">
                  {receivedAmount > 0 ? receivedAmount.toFixed(4) : '0.00'} TON
                </span>
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-2">
                <span>На кошелёк:</span>
                <span className="font-mono text-right break-all">{userDisplayAddress || toUserFriendlyAddress(userWallet)}</span>
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
              onClick={handleWithdraw}
              disabled={
                !amount ||
                parseFloat(amount) <= 0 ||
                parseFloat(amount) > currentBalance ||
                parseFloat(amount) < 1 ||
                isProcessing
              }
              className="flex-1 bg-orange-600 hover:bg-orange-700"
              data-testid="confirm-withdraw-btn"
            >
              {isProcessing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Обработка...
                </>
              ) : (
                <>
                  <ArrowUpFromLine className="w-4 h-4 mr-2" />
                  Запросить вывод
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
