import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Landmark, Building2, Coins, AlertCircle, Loader2, ChevronDown,
  Check, Clock, Percent, ArrowRight, Shield, Banknote, RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import PageHeader from '@/components/PageHeader';
import Sidebar from '@/components/Sidebar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

export default function CreditPage({ user }) {
  const navigate = useNavigate();
  const [loans, setLoans] = useState([]);
  const [totalDebt, setTotalDebt] = useState(0);
  const [businesses, setBusinesses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Apply modal
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [selectedBusiness, setSelectedBusiness] = useState('');
  const [creditCalc, setCreditCalc] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);
  const [lenderType, setLenderType] = useState('government');
  const [amount, setAmount] = useState('');
  const [deductionPercent, setDeductionPercent] = useState('');
  const [isApplying, setIsApplying] = useState(false);
  
  // Repay modal
  const [showRepayModal, setShowRepayModal] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState(null);
  const [repayAmount, setRepayAmount] = useState('');
  const [isRepaying, setIsRepaying] = useState(false);
  
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token) { navigate('/login'); return; }
    fetchData();
  }, [token]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [loansRes, bizRes] = await Promise.all([
        fetch(`${API}/credit/my-loans`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/my/businesses`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      if (loansRes.ok) {
        const data = await loansRes.json();
        setLoans(data.loans || []);
        setTotalDebt(data.total_debt || 0);
      }
      if (bizRes.ok) {
        const data = await bizRes.json();
        setBusinesses(data.businesses || []);
      }
    } catch (e) { console.error(e); }
    finally { setIsLoading(false); }
  };

  const calculateCredit = async (bizId) => {
    setCalcLoading(true);
    setCreditCalc(null);
    try {
      const res = await fetch(`${API}/credit/calculate/${bizId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCreditCalc(data);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка расчёта');
      }
    } catch (e) { toast.error('Ошибка расчёта'); }
    finally { setCalcLoading(false); }
  };

  const handleApply = async () => {
    if (!selectedBusiness || !amount || !deductionPercent) {
      toast.error('Заполните все поля');
      return;
    }
    setIsApplying(true);
    try {
      const res = await fetch(`${API}/credit/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          collateral_business_id: selectedBusiness,
          amount: parseFloat(amount),
          salary_deduction_percent: parseFloat(deductionPercent),
          lender_type: lenderType,
        })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка');
      }
      const data = await res.json();
      toast.success(`Кредит одобрен! Получено ${data.amount} TON`);
      setShowApplyModal(false);
      setSelectedBusiness('');
      setCreditCalc(null);
      setAmount('');
      setDeductionPercent('');
      fetchData();
    } catch (e) { toast.error(e.message); }
    finally { setIsApplying(false); }
  };

  const handleRepay = async () => {
    if (!selectedLoan) return;
    setIsRepaying(true);
    try {
      const payAmt = repayAmount ? parseFloat(repayAmount) : 0;
      const res = await fetch(`${API}/credit/repay/${selectedLoan.id}?amount=${payAmt}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка');
      }
      const data = await res.json();
      toast.success(data.status === 'paid' ? 'Кредит полностью погашен!' : `Оплачено ${data.paid_amount} TON`);
      setShowRepayModal(false);
      setRepayAmount('');
      fetchData();
    } catch (e) { toast.error(e.message); }
    finally { setIsRepaying(false); }
  };

  const maxDeduction = lenderType === 'government' ? 40 : 25;

  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-void">
        <Sidebar user={user} />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-cyber-cyan" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-void">
      <Sidebar user={user} />
      <main className="flex-1 p-4 lg:p-6 pt-4 lg:pt-6 lg:ml-16">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Header */}
          <PageHeader 
            icon={<Landmark className="w-6 h-6 text-amber-400" />}
            title="КРЕДИТОВАНИЕ"
            rightContent={
              <div className="flex gap-2">
                <Button onClick={fetchData} variant="outline" size="sm" className="border-white/10">
                  <RefreshCw className="w-4 h-4" />
                </Button>
                <Button
                  data-testid="apply-credit-btn"
                  onClick={() => setShowApplyModal(true)}
                  className="bg-amber-500 hover:bg-amber-600 text-black"
                  disabled={businesses.length === 0}
                >
                  <Banknote className="w-4 h-4 mr-1" />
                  <span className="hidden sm:inline">Взять кредит</span>
                </Button>
              </div>
            }
          />
          <p className="text-text-muted text-sm -mt-4">Займы от государства и банков</p>

          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-void border-amber-500/30">
              <CardContent className="p-4 flex items-center gap-3">
                <Coins className="w-8 h-8 text-amber-400" />
                <div>
                  <div className="text-2xl font-bold text-amber-400">{totalDebt.toFixed(2)}</div>
                  <div className="text-xs text-text-muted">Общий долг (TON)</div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-void border-green-500/30">
              <CardContent className="p-4 flex items-center gap-3">
                <Check className="w-8 h-8 text-green-400" />
                <div>
                  <div className="text-2xl font-bold text-green-400">
                    {loans.filter(l => l.status === 'paid').length}
                  </div>
                  <div className="text-xs text-text-muted">Погашено</div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-void border-red-500/30">
              <CardContent className="p-4 flex items-center gap-3">
                <AlertCircle className="w-8 h-8 text-red-400" />
                <div>
                  <div className="text-2xl font-bold text-red-400">
                    {loans.filter(l => l.status === 'overdue').length}
                  </div>
                  <div className="text-xs text-text-muted">Просрочено</div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Active Loans */}
          <div>
            <h2 className="text-lg font-bold text-white mb-3">Мои кредиты</h2>
            {loans.length === 0 ? (
              <Card className="bg-void border-white/10">
                <CardContent className="p-8 text-center">
                  <Landmark className="w-12 h-12 text-text-muted mx-auto mb-3" />
                  <p className="text-text-muted">У вас нет кредитов</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {loans.map(loan => (
                  <Card key={loan.id} className={`bg-void border ${
                    loan.status === 'overdue' ? 'border-red-500/50' :
                    loan.status === 'active' ? 'border-amber-500/30' :
                    loan.status === 'paid' ? 'border-green-500/30' : 'border-white/10'
                  }`}>
                    <CardContent className="p-4">
                      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge className={
                              loan.status === 'overdue' ? 'bg-red-500/20 text-red-400' :
                              loan.status === 'active' ? 'bg-amber-500/20 text-amber-400' :
                              loan.status === 'paid' ? 'bg-green-500/20 text-green-400' :
                              'bg-gray-500/20 text-gray-400'
                            }>
                              {loan.status === 'active' ? 'Активный' :
                               loan.status === 'overdue' ? 'Просрочен' :
                               loan.status === 'paid' ? 'Погашен' : 'Конфискован'}
                            </Badge>
                            <span className="text-xs text-text-muted">{loan.lender_name}</span>
                          </div>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
                            <div>
                              <div className="text-text-muted text-xs">Сумма</div>
                              <div className="text-white font-mono">{loan.amount} TON</div>
                            </div>
                            <div>
                              <div className="text-text-muted text-xs">Ставка</div>
                              <div className="text-white font-mono">{(loan.interest_rate * 100).toFixed(0)}%</div>
                            </div>
                            <div>
                              <div className="text-text-muted text-xs">Остаток</div>
                              <div className="text-amber-400 font-mono font-bold">{loan.remaining?.toFixed(2)} TON</div>
                            </div>
                            <div>
                              <div className="text-text-muted text-xs">Удержание</div>
                              <div className="text-white font-mono">{(loan.salary_deduction_percent * 100).toFixed(0)}%</div>
                            </div>
                          </div>
                          {/* Progress */}
                          {loan.total_debt > 0 && (
                            <div className="mt-2">
                              <Progress value={(loan.paid / loan.total_debt) * 100} className="h-1.5" />
                              <div className="text-xs text-text-muted mt-1">
                                Оплачено {loan.paid?.toFixed(2)} из {loan.total_debt?.toFixed(2)} TON
                              </div>
                            </div>
                          )}
                          {loan.status === 'overdue' && (
                            <div className="mt-2 text-red-400 text-xs flex items-center gap-1">
                              <AlertCircle className="w-3 h-3" />
                              Просрочен! Ставка удвоена. Бизнес может быть конфискован!
                            </div>
                          )}
                        </div>
                        {(loan.status === 'active' || loan.status === 'overdue') && (
                          <Button
                            data-testid={`repay-btn-${loan.id}`}
                            onClick={() => { setSelectedLoan(loan); setShowRepayModal(true); }}
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <Coins className="w-4 h-4 mr-1" />
                            Погасить
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Apply Credit Modal */}
      <Dialog open={showApplyModal} onOpenChange={setShowApplyModal}>
        <DialogContent className="bg-void border-amber-500/30 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Landmark className="w-5 h-5 text-amber-400" />
              Оформить кредит
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* Step 1: Select collateral business */}
            <div>
              <Label>1. Бизнес в залог</Label>
              <Select value={selectedBusiness} onValueChange={(v) => {
                setSelectedBusiness(v);
                setCreditCalc(null);
                setAmount('');
                calculateCredit(v);
              }}>
                <SelectTrigger className="bg-white/5 border-white/10 h-12" data-testid="collateral-select">
                  <SelectValue placeholder="Выберите бизнес..." />
                </SelectTrigger>
                <SelectContent>
                  {businesses.map(b => (
                    <SelectItem key={b.id} value={b.id}>
                      <div className="flex items-center gap-2">
                        <span>{b.config?.icon || '🏢'}</span>
                        <span>{b.config?.name?.ru || b.business_type} (Ур. {b.level})</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {calcLoading && <div className="flex justify-center py-4"><Loader2 className="w-6 h-6 animate-spin text-amber-400" /></div>}

            {creditCalc && (
              <>
                {/* Info */}
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-sm">
                  <div className="flex justify-between mb-1">
                    <span className="text-text-muted">Стоимость бизнеса + земля:</span>
                    <span className="text-white font-bold">{creditCalc.business_value} TON</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted">Максимальный кредит (30%):</span>
                    <span className="text-amber-400 font-bold">{creditCalc.max_credit} TON</span>
                  </div>
                </div>

                {/* Step 2: Lender */}
                <div>
                  <Label>2. Кредитор</Label>
                  <Select value={lenderType} onValueChange={(v) => {
                    setLenderType(v);
                    setDeductionPercent('');
                  }}>
                    <SelectTrigger className="bg-white/5 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="government">
                        <div className="flex items-center gap-2">
                          <Shield className="w-4 h-4 text-blue-400" />
                          Государство (ставка {(creditCalc.government.interest_rate * 100).toFixed(0)}%, макс. удержание {(creditCalc.government.max_salary_deduction * 100)}%)
                        </div>
                      </SelectItem>
                      {creditCalc.banks?.map(bank => (
                        <SelectItem key={bank.bank_id} value={bank.bank_id}>
                          <div className="flex items-center gap-2">
                            <Building2 className="w-4 h-4 text-amber-400" />
                            Банк Ур.{bank.level} (ставка {(bank.interest_rate * 100).toFixed(0)}%, удерж. до 25%)
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Step 3: Amount */}
                <div>
                  <Label>3. Сумма кредита (TON)</Label>
                  <Input
                    data-testid="credit-amount-input"
                    type="number"
                    step="0.01"
                    min="0.01"
                    max={creditCalc.max_credit}
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder={`До ${creditCalc.max_credit} TON`}
                    className="bg-white/5 border-white/10"
                  />
                  {amount && parseFloat(amount) > 0 && (
                    <div className="text-xs text-text-muted mt-1">
                      Вернуть с процентами: <span className="text-amber-400 font-bold">
                        {(parseFloat(amount) * (1 + (lenderType === 'government' ? creditCalc.government.interest_rate : (creditCalc.banks?.find(b => b.bank_id === lenderType)?.interest_rate || 0.20)))).toFixed(2)} TON
                      </span>
                    </div>
                  )}
                </div>

                {/* Step 4: Deduction */}
                <div>
                  <Label>4. Процент удержания с дохода ({maxDeduction}% макс.)</Label>
                  <Input
                    data-testid="deduction-input"
                    type="number"
                    min="1"
                    max={maxDeduction}
                    step="1"
                    value={deductionPercent}
                    onChange={(e) => setDeductionPercent(e.target.value)}
                    placeholder={`От 1% до ${maxDeduction}%`}
                    className="bg-white/5 border-white/10"
                  />
                </div>

                {/* Warning */}
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-xs text-red-300">
                  <AlertCircle className="w-4 h-4 inline mr-1" />
                  При неуплате в течение 7 дней ваш бизнес и земля будут конфискованы!
                </div>
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApplyModal(false)} className="border-white/10">Отмена</Button>
            <Button
              data-testid="apply-credit-submit"
              onClick={handleApply}
              disabled={!creditCalc || !amount || !deductionPercent || isApplying}
              className="bg-amber-500 hover:bg-amber-600 text-black"
            >
              {isApplying ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Banknote className="w-4 h-4 mr-2" />}
              Оформить кредит
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Repay Modal */}
      <Dialog open={showRepayModal} onOpenChange={setShowRepayModal}>
        <DialogContent className="bg-void border-green-500/30">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Coins className="w-5 h-5 text-green-400" />
              Погасить кредит
            </DialogTitle>
          </DialogHeader>
          {selectedLoan && (
            <div className="space-y-4">
              <div className="bg-white/5 rounded-lg p-3 text-sm space-y-2">
                <div className="flex justify-between">
                  <span className="text-text-muted">Остаток долга:</span>
                  <span className="text-amber-400 font-bold">{selectedLoan.remaining?.toFixed(2)} TON</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Кредитор:</span>
                  <span className="text-white">{selectedLoan.lender_name}</span>
                </div>
              </div>
              <div>
                <Label>Сумма погашения (пусто = полное)</Label>
                <Input
                  data-testid="repay-amount-input"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={repayAmount}
                  onChange={(e) => setRepayAmount(e.target.value)}
                  placeholder={`Полное: ${selectedLoan.remaining?.toFixed(2)} TON`}
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRepayModal(false)} className="border-white/10">Отмена</Button>
            <Button
              data-testid="repay-submit"
              onClick={handleRepay}
              disabled={isRepaying}
              className="bg-green-600 hover:bg-green-700"
            >
              {isRepaying ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Погасить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
