/**
 * TransactionHistoryPage - User transaction history
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  History, ArrowUpRight, ArrowDownRight, ChevronLeft, ChevronRight,
  Filter, Calendar, X, ExternalLink, Wallet, Building2,
  Package, Users, ShieldCheck, Truck
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import Sidebar from '@/components/Sidebar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const TYPE_ICONS = {
  deposit: <ArrowDownRight className="w-5 h-5 text-green-400" />,
  withdrawal: <ArrowUpRight className="w-5 h-5 text-red-400" />,
  land_purchase: <Building2 className="w-5 h-5 text-blue-400" />,
  business_build: <Building2 className="w-5 h-5 text-purple-400" />,
  resource_sale: <Package className="w-5 h-5 text-green-400" />,
  resource_purchase: <Package className="w-5 h-5 text-orange-400" />,
  patron_fee: <Users className="w-5 h-5 text-yellow-400" />,
  warehouse_purchase: <Truck className="w-5 h-5 text-blue-400" />,
  default: <Wallet className="w-5 h-5 text-text-muted" />,
};

export default function TransactionHistoryPage({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });
  const [typeFilter, setTypeFilter] = useState('all');
  const [types, setTypes] = useState({});
  const [summary, setSummary] = useState(null);
  
  const [selectedTx, setSelectedTx] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  
  const token = localStorage.getItem('token');

  const fetchTransactions = useCallback(async (page = 1) => {
    if (!token) {
      navigate('/auth?mode=login');
      return;
    }
    
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 20 });
      if (typeFilter !== 'all') params.append('type_filter', typeFilter);
      
      const res = await fetch(`${BACKEND_URL}/api/history/transactions?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setTransactions(data.transactions);
        setPagination(data.pagination);
      }
    } catch (e) {
      console.error('Fetch transactions error:', e);
    } finally {
      setLoading(false);
    }
  }, [token, navigate, typeFilter]);

  const fetchTypes = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/history/types`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTypes(data.types);
      }
    } catch (e) {
      console.error('Fetch types error:', e);
    }
  }, [token]);

  const fetchSummary = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/history/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSummary(data);
      }
    } catch (e) {
      console.error('Fetch summary error:', e);
    }
  }, [token]);

  useEffect(() => {
    fetchTypes();
    fetchSummary();
  }, [fetchTypes, fetchSummary]);

  useEffect(() => {
    fetchTransactions(1);
  }, [fetchTransactions, typeFilter]);

  const openDetails = async (txId) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/history/transactions/${txId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedTx(data);
        setShowDetails(true);
      }
    } catch (e) {
      toast.error('Ошибка загрузки деталей');
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAmount = (amount) => {
    if (amount === undefined || amount === null || isNaN(amount)) {
      return <span className="text-text-muted">0.00 TON</span>;
    }
    const numAmount = Number(amount);
    const isPositive = numAmount > 0;
    const absAmount = Math.abs(numAmount);
    return (
      <span className={isPositive ? 'text-green-400' : 'text-red-400'}>
        {isPositive ? '+' : '-'}{absAmount.toFixed(2)} TON
      </span>
    );
  };

  return (
    <div className="flex h-screen bg-void">
      <Sidebar user={user} />
      
      <div className="flex-1 overflow-auto lg:ml-16">
        <div className="relative min-h-screen font-rajdhani pb-20 lg:pb-0">
          {/* Background grid */}
          <div className="absolute inset-0 opacity-10 pointer-events-none">
            <div 
              className="absolute inset-0"
              style={{
                backgroundImage: `
                  linear-gradient(rgba(0, 240, 255, 0.1) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(0, 240, 255, 0.1) 1px, transparent 1px)
                `,
                backgroundSize: '50px 50px',
              }}
            />
          </div>

          {/* Main Content */}
          <div className="relative z-10 container mx-auto px-4 sm:px-6 py-6 sm:py-12 max-w-4xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <History className="w-8 h-8 text-cyber-cyan" />
                  <div>
                    <h1 className="font-unbounded text-xl sm:text-2xl font-bold text-white uppercase tracking-tight">
                      История операций
                    </h1>
                    <p className="text-text-muted text-sm">
                      Все ваши транзакции
                    </p>
                  </div>
                </div>
                
                {/* Filter */}
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger className="w-40 bg-panel border-white/10 text-white">
                    <Filter className="w-4 h-4 mr-2" />
                    <SelectValue placeholder="Фильтр" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Все операции</SelectItem>
                    {Object.entries(types).map(([key, info]) => (
                      <SelectItem key={key} value={key}>
                        {info.icon} {info.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Transaction List */}
              <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden">
                {loading ? (
                  <div className="p-8 text-center text-text-muted">
                    Загрузка...
                  </div>
                ) : transactions.length === 0 ? (
                  <div className="p-8 text-center text-text-muted">
                    <History className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p>Нет операций</p>
                  </div>
                ) : (
                  <div className="divide-y divide-white/5">
                    {transactions.map((tx) => (
                      <button
                        key={tx.id}
                        onClick={() => openDetails(tx.id)}
                        data-testid={`tx-${tx.id}`}
                        className="w-full p-4 flex items-center gap-4 hover:bg-white/5 transition-colors text-left"
                      >
                        {/* Icon */}
                        <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center flex-shrink-0">
                          {TYPE_ICONS[tx.type] || TYPE_ICONS.default}
                        </div>
                        
                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <p className="text-white font-medium truncate">
                            {tx.type_icon} {tx.type_name}
                          </p>
                          <p className="text-text-muted text-xs">
                            {formatDate(tx.created_at)}
                          </p>
                        </div>
                        
                        {/* Amount */}
                        <div className="text-right">
                          {formatAmount(tx.amount)}
                        </div>
                        
                        <ExternalLink className="w-4 h-4 text-text-muted" />
                      </button>
                    ))}
                  </div>
                )}
                
                {/* Pagination */}
                {pagination.pages > 1 && (
                  <div className="p-4 border-t border-white/5 flex items-center justify-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchTransactions(pagination.page - 1)}
                      disabled={pagination.page <= 1}
                      className="border-white/10"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="text-text-muted text-sm px-4">
                      {pagination.page} / {pagination.pages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchTransactions(pagination.page + 1)}
                      disabled={pagination.page >= pagination.pages}
                      className="border-white/10"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Transaction Details Dialog */}
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogContent className="bg-panel border-white/10 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white font-unbounded">
              Детали операции
            </DialogTitle>
          </DialogHeader>
          
          {selectedTx && (
            <div className="space-y-4">
              {/* Type and Amount */}
              <div className="text-center p-4 bg-white/5 rounded-xl">
                <p className="text-text-muted text-sm mb-2">
                  {selectedTx.type_icon} {selectedTx.type_name}
                </p>
                <p className={`text-3xl font-bold ${(selectedTx.amount || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {(selectedTx.amount || 0) >= 0 ? '+' : ''}{(selectedTx.amount || selectedTx.amount_ton || 0).toFixed(2)} TON
                </p>
              </div>
              
              {/* Date */}
              <div className="flex justify-between p-3 bg-white/5 rounded-lg">
                <span className="text-text-muted">Дата</span>
                <span className="text-white">{formatDate(selectedTx.created_at)}</span>
              </div>
              
              {/* ID */}
              <div className="flex justify-between p-3 bg-white/5 rounded-lg">
                <span className="text-text-muted">ID</span>
                <span className="text-white font-mono text-xs truncate max-w-40">
                  {selectedTx.id}
                </span>
              </div>
              
              {/* Details */}
              {selectedTx.details && Object.keys(selectedTx.details).length > 0 && (
                <div className="space-y-2">
                  <p className="text-text-muted text-xs uppercase">Детали</p>
                  {Object.entries(selectedTx.details).map(([key, value]) => (
                    <div key={key} className="flex justify-between p-3 bg-white/5 rounded-lg">
                      <span className="text-text-muted capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="text-white text-sm truncate max-w-40">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
