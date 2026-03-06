import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Calculator, TrendingUp, Factory, Zap, Building2 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { getResource } from '@/lib/resourceConfig';
import Sidebar from '@/components/Sidebar';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TIER_COLORS = {
  1: { bg: 'from-green-900/40 to-green-800/20', border: 'border-green-500/30', badge: 'bg-green-500/20 text-green-400', label: 'I Эшелон: Ресурсы' },
  2: { bg: 'from-yellow-900/40 to-yellow-800/20', border: 'border-yellow-500/30', badge: 'bg-yellow-500/20 text-yellow-400', label: 'II Эшелон: Производство' },
  3: { bg: 'from-red-900/40 to-red-800/20', border: 'border-red-500/30', badge: 'bg-red-500/20 text-red-400', label: 'III Эшелон: Инфраструктура' },
};

export default function IncomeTablePage({ user }) {
  const navigate = useNavigate();
  const [incomeTable, setIncomeTable] = useState(null);
  const [selectedBusiness, setSelectedBusiness] = useState('helios');
  const [selectedTier, setSelectedTier] = useState('all');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadIncomeTable();
  }, []);

  const loadIncomeTable = async () => {
    try {
      const response = await axios.get(`${API}/stats/income-table?lang=ru`);
      setIncomeTable(response.data.income_table);
      if (response.data.income_table) {
        const first = Object.keys(response.data.income_table)[0];
        if (first) setSelectedBusiness(first);
      }
    } catch (error) {
      console.error('Failed to load income table:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getLevelData = () => {
    if (!incomeTable || !incomeTable[selectedBusiness]) return [];
    const biz = incomeTable[selectedBusiness];
    const levels = biz.levels || {};
    return Object.values(levels).sort((a, b) => a.level - b.level);
  };

  const getBusinessesByTier = (tier) => {
    if (!incomeTable) return [];
    return Object.entries(incomeTable)
      .filter(([_, v]) => selectedTier === 'all' || v.tier === tier)
      .filter(([_, v]) => v.tier === tier)
      .map(([key, v]) => ({ value: key, label: `${v.icon} ${v.name}`, tier: v.tier }));
  };

  const bizData = incomeTable?.[selectedBusiness];
  const levelData = getLevelData();

  if (isLoading) {
    return (
      <div className="flex h-screen bg-void">
        <Sidebar user={user} />
        <div className="flex-1 flex items-center justify-center lg:ml-16">
          <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-void">
      <Sidebar user={user} />
      
      <div className="flex-1 overflow-hidden lg:ml-16">
        <ScrollArea className="h-full">
          <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 pb-24">
            {/* Header */}
            <div className="sticky top-0 z-10 bg-gray-950/90 backdrop-blur border-b border-gray-800 px-4 py-3">
              <div className="max-w-6xl mx-auto flex items-center gap-3">
                <Calculator className="w-5 h-5 text-cyan-400" />
                <h1 className="text-lg font-bold text-white">Калькулятор доходов V2.0</h1>
              </div>
            </div>

      <div className="max-w-6xl mx-auto p-4 space-y-6">
        {/* Tier Filter */}
        <div className="flex flex-wrap gap-2">
          {['all', 1, 2, 3].map(tier => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                selectedTier === tier
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                  : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:bg-gray-700/50'
              }`}
            >
              {tier === 'all' ? '🏢 Все' : `${tier === 1 ? '🟢' : tier === 2 ? '🟡' : '🔴'} Tier ${tier}`}
            </button>
          ))}
        </div>

        {/* Business Selector by Tier */}
        {[1, 2, 3].filter(t => selectedTier === 'all' || selectedTier === t).map(tier => {
          const bizList = getBusinessesByTier(tier);
          if (!bizList.length) return null;
          const tc = TIER_COLORS[tier];
          return (
            <div key={tier} className="space-y-3">
              <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${tc.badge} text-xs font-bold`}>
                {tc.label}
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {bizList.map(biz => (
                  <button
                    key={biz.value}
                    onClick={() => setSelectedBusiness(biz.value)}
                    className={`p-3 rounded-xl text-left transition-all border ${
                      selectedBusiness === biz.value
                        ? `bg-gradient-to-br ${tc.bg} ${tc.border} shadow-lg`
                        : 'bg-gray-800/30 border-gray-700/50 hover:bg-gray-800/60'
                    }`}
                  >
                    <span className="text-sm">{biz.label}</span>
                  </button>
                ))}
              </div>
            </div>
          );
        })}

        {/* Selected Business Details */}
        {bizData && (
          <motion.div
            key={selectedBusiness}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            {/* Business Header */}
            <div className={`p-4 rounded-2xl border bg-gradient-to-br ${TIER_COLORS[bizData.tier]?.bg} ${TIER_COLORS[bizData.tier]?.border}`}>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-3xl">{bizData.icon}</span>
                <div>
                  <h2 className="text-xl font-bold text-white">{bizData.name}</h2>
                  <div className="flex gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${TIER_COLORS[bizData.tier]?.badge}`}>
                      Tier {bizData.tier}
                    </span>
                    {bizData.produces && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400">
                        {getResource(bizData.produces).icon} Производит: {getResource(bizData.produces).name}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              {bizData.consumes && bizData.consumes.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  <span className="text-xs text-gray-400">Потребляет:</span>
                  {bizData.consumes.map(r => (
                    <span key={r} className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400">
                      {getResource(r).icon} {getResource(r).name}
                    </span>
                  ))}
                </div>
              )}
              {/* Patronage Info */}
              {bizData.is_patron && bizData.patron_effect && (
                <div className="mt-3 p-2 rounded-xl bg-amber-900/20 border border-amber-700/30">
                  <div className="text-xs text-amber-300 font-bold">👑 Покровитель</div>
                  <div className="text-xs text-gray-400 mt-1">
                    Бонус: +{((bizData.patron_effect.bonus || 0) * 100).toFixed(0)}% ({bizData.patron_effect.type})
                    <br />{bizData.patron_effect.description}
                  </div>
                </div>
              )}
            </div>

            {/* Level Table */}
            <div className="overflow-x-auto rounded-xl border border-gray-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-800/60 text-gray-400">
                    <th className="px-3 py-2 text-left">Ур.</th>
                    <th className="px-3 py-2 text-right">Произв.</th>
                    <th className="px-3 py-2 text-right">Затраты</th>
                    <th className="px-3 py-2 text-right">Доход/день</th>
                    <th className="px-3 py-2 text-right">Налог/день</th>
                    <th className="px-3 py-2 text-right">Обслуж.</th>
                    <th className="px-3 py-2 text-right text-green-400">Чистый/день</th>
                    <th className="px-3 py-2 text-right">Месяц</th>
                    <th className="px-3 py-2 text-right">Склад</th>
                    <th className="px-3 py-2 text-right">Износ%</th>
                  </tr>
                </thead>
                <tbody>
                  {levelData.map((row, i) => (
                    <tr
                      key={row.level}
                      className={`border-t border-gray-800/50 ${i % 2 === 0 ? 'bg-gray-900/30' : 'bg-gray-900/10'} hover:bg-gray-800/40 transition-colors`}
                    >
                      <td className="px-3 py-2 font-bold text-cyan-400">{row.level}</td>
                      <td className="px-3 py-2 text-right text-white font-mono">{row.production?.toLocaleString()}</td>
                      <td className="px-3 py-2 text-right text-red-400 font-mono">{row.consumption_total?.toLocaleString()}</td>
                      <td className="px-3 py-2 text-right text-yellow-400 font-mono">{row.gross_daily_ton?.toFixed(2)}</td>
                      <td className="px-3 py-2 text-right text-red-400 font-mono">{row.tax_daily_ton?.toFixed(2)}</td>
                      <td className="px-3 py-2 text-right text-orange-400 font-mono">{row.maintenance_daily_ton?.toFixed(2)}</td>
                      <td className="px-3 py-2 text-right font-bold font-mono" style={{color: (row.net_daily_ton || 0) >= 0 ? '#4ade80' : '#f87171'}}>
                        {row.net_daily_ton?.toFixed(2)} TON
                      </td>
                      <td className="px-3 py-2 text-right text-emerald-400 font-mono">{row.monthly_ton?.toFixed(1)}</td>
                      <td className="px-3 py-2 text-right text-gray-400">{row.storage_capacity}</td>
                      <td className="px-3 py-2 text-right text-orange-300">{row.daily_wear_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Consumption Breakdown for Level 1 */}
            {levelData[0]?.consumption_breakdown && Object.keys(levelData[0].consumption_breakdown).length > 0 && (
              <div className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/50">
                <h3 className="text-sm font-bold text-gray-300 mb-2">📦 Разбивка затрат (Уровень 1)</h3>
                <div className="flex flex-wrap gap-3">
                  {Object.entries(levelData[0].consumption_breakdown).map(([res, amount]) => (
                    <div key={res} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-900/50">
                      <span>{getResource(res).icon}</span>
                      <span className="text-sm text-gray-300">{getResource(res).name}:</span>
                      <span className="text-sm font-bold text-white">{amount}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="p-4 rounded-xl bg-green-900/20 border border-green-800/30">
            <div className="text-green-400 font-bold text-sm mb-1">🟢 Tier I: Ресурсы</div>
            <div className="text-xs text-gray-400">Налог 15% • Окупаемость 12-18 дней</div>
            <div className="text-xs text-gray-500 mt-1">Производят базовые ресурсы: энергию, кварц, трафик</div>
          </div>
          <div className="p-4 rounded-xl bg-yellow-900/20 border border-yellow-800/30">
            <div className="text-yellow-400 font-bold text-sm mb-1">🟡 Tier II: Производство</div>
            <div className="text-xs text-gray-400">Налог 23% • Окупаемость 20-30 дней</div>
            <div className="text-xs text-gray-500 mt-1">Перерабатывают сырье в чипы, NFT, нейро-код</div>
          </div>
          <div className="p-4 rounded-xl bg-red-900/20 border border-red-800/30">
            <div className="text-red-400 font-bold text-sm mb-1">🔴 Tier III: Инфраструктура</div>
            <div className="text-xs text-gray-400">Налог 30% • Окупаемость 35-50 дней</div>
            <div className="text-xs text-gray-500 mt-1">Генерируют прямой доход в TON</div>
          </div>
        </div>
      </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
