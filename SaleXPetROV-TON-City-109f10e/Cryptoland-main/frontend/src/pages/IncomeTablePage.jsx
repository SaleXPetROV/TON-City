import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Calculator, TrendingUp, Building2, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useTranslation } from '@/lib/translations';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function IncomeTablePage() {
  const navigate = useNavigate();
  const [lang, setLang] = useState(localStorage.getItem('ton_city_lang') || 'en');
  const { t } = useTranslation(lang);
  
  const [incomeTable, setIncomeTable] = useState(null);
  const [selectedBusiness, setSelectedBusiness] = useState('farm');
  const [selectedZone, setSelectedZone] = useState('center');
  const [selectedConnections, setSelectedConnections] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadIncomeTable();
  }, [lang]);

  const loadIncomeTable = async () => {
    try {
      const response = await axios.get(`${API}/stats/income-table?lang=${lang}`);
      setIncomeTable(response.data.income_table);
    } catch (error) {
      console.error('Failed to load income table:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getFilteredData = () => {
    if (!incomeTable || !incomeTable[selectedBusiness]) return [];
    
    const bizData = incomeTable[selectedBusiness];
    const levels = bizData.levels || {};
    
    return Object.values(levels).filter(item => 
      item.zone === selectedZone && item.connections === selectedConnections
    ).sort((a, b) => a.level - b.level);
  };

  const businessOptions = incomeTable ? Object.entries(incomeTable).map(([key, value]) => ({
    value: key,
    label: `${value.icon} ${value.name}`,
    sector: value.sector
  })) : [];

  const zones = ['center', 'business', 'residential', 'industrial', 'outskirts'];
  const connections = [0, 1, 2, 3, 5];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  const filteredData = getFilteredData();
  const selectedBizInfo = incomeTable?.[selectedBusiness];

  return (
    <div className="min-h-screen bg-void">
      {/* Header */}
      <header className="glass-panel border-b border-grid-border px-6 py-4">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(-1)}
              className="text-text-muted hover:text-text-main"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('back')}
            </Button>
            <h1 className="font-unbounded text-xl font-bold text-text-main flex items-center gap-2">
              <Calculator className="w-5 h-5 text-cyber-cyan" />
              {t('incomeTable')}
            </h1>
          </div>
          
          {/* Language selector */}
          <Select value={lang} onValueChange={(v) => { setLang(v); localStorage.setItem('ton_city_lang', v); }}>
            <SelectTrigger className="w-32 bg-panel border-grid-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en">🇬🇧 English</SelectItem>
              <SelectItem value="ru">🇷🇺 Русский</SelectItem>
              <SelectItem value="zh">🇨🇳 中文</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel rounded-2xl p-6 mb-8"
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Business selector */}
            <div>
              <label className="text-text-muted text-sm mb-2 block">Business Type</label>
              <Select value={selectedBusiness} onValueChange={setSelectedBusiness}>
                <SelectTrigger className="bg-panel border-grid-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {businessOptions.map((biz) => (
                    <SelectItem key={biz.value} value={biz.value}>
                      {biz.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Zone selector */}
            <div>
              <label className="text-text-muted text-sm mb-2 block">{t('zone')}</label>
              <Select value={selectedZone} onValueChange={setSelectedZone}>
                <SelectTrigger className="bg-panel border-grid-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {zones.map((zone) => (
                    <SelectItem key={zone} value={zone}>
                      {t(zone)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Connections selector */}
            <div>
              <label className="text-text-muted text-sm mb-2 block">{t('connections')}</label>
              <Select value={selectedConnections.toString()} onValueChange={(v) => setSelectedConnections(parseInt(v))}>
                <SelectTrigger className="bg-panel border-grid-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {connections.map((c) => (
                    <SelectItem key={c} value={c.toString()}>
                      {c} {t('connections')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Business info */}
            {selectedBizInfo && (
              <div className="glass-panel rounded-lg p-4">
                <div className="text-4xl mb-2">{selectedBizInfo.icon}</div>
                <div className="font-unbounded text-text-main">{selectedBizInfo.name}</div>
                <div className="text-sm text-cyber-cyan font-mono">Cost: {selectedBizInfo.cost} TON</div>
                <div className="text-xs text-text-muted">{t(selectedBizInfo.sector)}</div>
              </div>
            )}
          </div>
        </motion.div>

        {/* Income Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-panel rounded-2xl p-6"
        >
          <h2 className="font-unbounded text-lg font-bold text-text-main mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-success" />
            Income by Level
          </h2>

          {filteredData.length === 0 ? (
            <div className="text-center py-12 text-text-muted">
              <Building2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>This business type is not available in the selected zone</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-grid-border">
                    <th className="text-left py-3 px-4 text-text-muted font-rajdhani">{t('level')}</th>
                    <th className="text-right py-3 px-4 text-text-muted font-rajdhani">{t('grossDaily')}</th>
                    <th className="text-right py-3 px-4 text-text-muted font-rajdhani">{t('netDaily')}</th>
                    <th className="text-right py-3 px-4 text-text-muted font-rajdhani">{t('monthly')}</th>
                    <th className="text-right py-3 px-4 text-text-muted font-rajdhani">{t('roiDays')}</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((row, index) => (
                    <motion.tr
                      key={row.level}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="border-b border-grid-border/50 hover:bg-panel/50"
                    >
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-2">
                          <span className={`w-8 h-8 rounded-full flex items-center justify-center font-mono font-bold ${
                            row.level >= 8 ? 'bg-signal-amber text-black' :
                            row.level >= 5 ? 'bg-cyber-cyan text-black' :
                            'bg-panel text-text-main'
                          }`}>
                            {row.level}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-text-main">
                        {row.gross_daily.toFixed(2)} TON
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-success">
                        {row.net_daily.toFixed(2)} TON
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-signal-amber">
                        {row.monthly.toFixed(2)} TON
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-cyber-cyan">
                        {row.roi_days < 999 ? `${row.roi_days} days` : '-'}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>

        {/* Info cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-panel rounded-xl p-6"
          >
            <h3 className="font-unbounded text-text-main mb-3">Tax Rate</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-muted">Base</span>
                <span className="text-success font-mono">13%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">&gt;15% market</span>
                <span className="text-signal-amber font-mono">18%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">&gt;20% market</span>
                <span className="text-error font-mono">25%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">&gt;25% market</span>
                <span className="text-error font-mono">35%</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-panel rounded-xl p-6"
          >
            <h3 className="font-unbounded text-text-main mb-3">Commissions</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-muted">Plot resale</span>
                <span className="text-signal-amber font-mono">15%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Resource trade</span>
                <span className="text-signal-amber font-mono">5%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Rental</span>
                <span className="text-signal-amber font-mono">10%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Withdrawal</span>
                <span className="text-signal-amber font-mono">3% + network</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-panel rounded-xl p-6"
          >
            <h3 className="font-unbounded text-text-main mb-3">Connection Bonus</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-muted">0 connections</span>
                <span className="text-text-main font-mono">×1.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">1 connection</span>
                <span className="text-success font-mono">×1.2 (+20%)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">2 connections</span>
                <span className="text-success font-mono">×1.4 (+40%)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">5 connections</span>
                <span className="text-success font-mono">×2.0 (+100%)</span>
              </div>
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
