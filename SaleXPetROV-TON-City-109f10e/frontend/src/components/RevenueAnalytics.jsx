import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { DollarSign, TrendingUp, Building2, MapPin, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function RevenueAnalytics({ token }) {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API}/admin/revenue-stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load revenue stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !stats) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neon-blue"></div>
      </div>
    );
  }

  const revenueItems = [
    {
      title: 'Продажа участков',
      value: stats.plot_sales_income || 0,
      count: stats.total_plot_sales || 0,
      icon: MapPin,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/30'
    },
    {
      title: 'Продажа зданий',
      value: stats.building_sales_income || 0,
      count: stats.total_buildings_sold || 0,
      icon: Building2,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
      borderColor: 'border-purple-500/30'
    },
    {
      title: 'Налоги',
      value: stats.total_tax || 0,
      count: null,
      icon: DollarSign,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/10',
      borderColor: 'border-yellow-500/30'
    },
    {
      title: 'Комиссии за выводы',
      value: stats.withdrawal_fees || 0,
      count: stats.total_withdrawals || 0,
      icon: TrendingUp,
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/30'
    },
  ];

  const totalRevenue = revenueItems.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="space-y-6">
      {/* Total Revenue */}
      <Card className="bg-gradient-to-br from-green-500/20 to-blue-500/20 border-green-500/30">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DollarSign className="w-6 h-6 text-green-400" />
              <span>Общий доход</span>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={loadStats}
              className="border-white/20"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </CardTitle>
          <CardDescription>Все источники дохода администратора</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-4xl font-bold text-green-400">
            {totalRevenue.toFixed(2)} TON
          </div>
        </CardContent>
      </Card>

      {/* Revenue Breakdown */}
      <div className="grid gap-4 md:grid-cols-2">
        {revenueItems.map((item, index) => (
          <Card
            key={index}
            className={`${item.bgColor} ${item.borderColor} border`}
            data-testid={`revenue-${item.title.toLowerCase().replace(/\s+/g, '-')}`}
          >
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-lg">
                <div className="flex items-center gap-2">
                  <item.icon className={`w-5 h-5 ${item.color}`} />
                  <span>{item.title}</span>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-3xl font-bold ${item.color} mb-2`}>
                {item.value.toFixed(2)} TON
              </div>
              {item.count !== null && (
                <div className="text-sm text-gray-400">
                  Транзакций: {item.count}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Deposits Info */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader>
          <CardTitle>Статистика пополнений</CardTitle>
          <CardDescription>Информация о входящих платежах</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <div className="text-sm text-gray-400 mb-1">Всего пополнений</div>
              <div className="text-2xl font-bold text-white">
                {(stats.total_deposits || 0).toFixed(2)} TON
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Количество</div>
              <div className="text-2xl font-bold text-white">
                {stats.deposits_count || 0}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Средний чек</div>
              <div className="text-2xl font-bold text-white">
                {stats.deposits_count > 0
                  ? ((stats.total_deposits || 0) / stats.deposits_count).toFixed(2)
                  : '0.00'} TON
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
