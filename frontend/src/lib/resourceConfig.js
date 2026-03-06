/**
 * TON-City Resource Configuration V2.0
 * All 16 resources with icons, prices (min 0.01 TON), and styling
 */

export const RESOURCES = {
  energy: {
    id: 'energy',
    name: 'Энергия',
    nameEn: 'Energy',
    icon: '⚡',
    color: '#fbbf24',
    bgColor: 'bg-amber-500/20',
    borderColor: 'border-amber-500/50',
    textColor: 'text-amber-400',
    basePrice: 0.01,
    unit: 'кВт',
    tier: 1,
    description: 'Базовый ресурс для работы всех зданий'
  },
  cu: {
    id: 'cu',
    name: 'Мощность',
    nameEn: 'Compute',
    icon: '🖥️',
    color: '#3b82f6',
    bgColor: 'bg-blue-500/20',
    borderColor: 'border-blue-500/50',
    textColor: 'text-blue-400',
    basePrice: 0.02,
    unit: 'TH/s',
    tier: 1,
    description: 'Вычислительная мощность для ИИ и NFT'
  },
  quartz: {
    id: 'quartz',
    name: 'Кварц',
    nameEn: 'Quartz',
    icon: '💎',
    color: '#8b5cf6',
    bgColor: 'bg-violet-500/20',
    borderColor: 'border-violet-500/50',
    textColor: 'text-violet-400',
    basePrice: 0.015,
    unit: 'кг',
    tier: 1,
    description: 'Кристаллы для производства микросхем'
  },
  traffic: {
    id: 'traffic',
    name: 'Трафик',
    nameEn: 'Traffic',
    icon: '📡',
    color: '#06b6d4',
    bgColor: 'bg-cyan-500/20',
    borderColor: 'border-cyan-500/50',
    textColor: 'text-cyan-400',
    basePrice: 0.012,
    unit: 'GB',
    tier: 1,
    description: 'Сетевой трафик для коммуникаций'
  },
  cooling: {
    id: 'cooling',
    name: 'Холод',
    nameEn: 'Cooling',
    icon: '❄️',
    color: '#22d3ee',
    bgColor: 'bg-sky-500/20',
    borderColor: 'border-sky-500/50',
    textColor: 'text-sky-400',
    basePrice: 0.02,
    unit: 'BTU',
    tier: 1,
    description: 'Охлаждение для серверов и оборудования'
  },
  biomass: {
    id: 'biomass',
    name: 'Био-масса',
    nameEn: 'Biomass',
    icon: '🌿',
    color: '#22c55e',
    bgColor: 'bg-green-500/20',
    borderColor: 'border-green-500/50',
    textColor: 'text-green-400',
    basePrice: 0.018,
    unit: 'кг',
    tier: 1,
    description: 'Органическое сырье для кафе и арены'
  },
  scrap: {
    id: 'scrap',
    name: 'Вторсырье',
    nameEn: 'Scrap',
    icon: '🗑️',
    color: '#78716c',
    bgColor: 'bg-stone-500/20',
    borderColor: 'border-stone-500/50',
    textColor: 'text-stone-400',
    basePrice: 0.01,
    unit: 'кг',
    tier: 1,
    description: 'Переработанные материалы для ремзоны'
  },
  chips: {
    id: 'chips',
    name: 'Чипы',
    nameEn: 'Chips',
    icon: '🔲',
    color: '#f97316',
    bgColor: 'bg-orange-500/20',
    borderColor: 'border-orange-500/50',
    textColor: 'text-orange-400',
    basePrice: 0.10,
    unit: 'шт',
    tier: 2,
    description: 'Микросхемы для электроники'
  },
  nft: {
    id: 'nft',
    name: 'NFT',
    nameEn: 'NFT',
    icon: '🎨',
    color: '#ec4899',
    bgColor: 'bg-pink-500/20',
    borderColor: 'border-pink-500/50',
    textColor: 'text-pink-400',
    basePrice: 0.15,
    unit: 'шт',
    tier: 2,
    description: 'Цифровые коллекции для банков и казино'
  },
  neurocode: {
    id: 'neurocode',
    name: 'Нейро-код',
    nameEn: 'Neuro-code',
    icon: '🧠',
    color: '#a855f7',
    bgColor: 'bg-purple-500/20',
    borderColor: 'border-purple-500/50',
    textColor: 'text-purple-400',
    basePrice: 0.20,
    unit: 'шт',
    tier: 2,
    description: 'AI-алгоритмы для валидаторов и бирж'
  },
  logistics: {
    id: 'logistics',
    name: 'Доставка',
    nameEn: 'Delivery',
    icon: '🚚',
    color: '#14b8a6',
    bgColor: 'bg-teal-500/20',
    borderColor: 'border-teal-500/50',
    textColor: 'text-teal-400',
    basePrice: 0.05,
    unit: 'слот',
    tier: 2,
    description: 'Транспортировка товаров'
  },
  repair_kits: {
    id: 'repair_kits',
    name: 'Ремкомплекты',
    nameEn: 'Repair Kits',
    icon: '🔧',
    color: '#6b7280',
    bgColor: 'bg-gray-500/20',
    borderColor: 'border-gray-500/50',
    textColor: 'text-gray-400',
    basePrice: 0.08,
    unit: 'шт',
    tier: 2,
    description: 'Для восстановления прочности зданий'
  },
  vr_experience: {
    id: 'vr_experience',
    name: 'VR-опыт',
    nameEn: 'VR Experience',
    icon: '🥽',
    color: '#e879f9',
    bgColor: 'bg-fuchsia-500/20',
    borderColor: 'border-fuchsia-500/50',
    textColor: 'text-fuchsia-400',
    basePrice: 0.12,
    unit: 'шт',
    tier: 2,
    description: 'Виртуальный опыт для казино и арены'
  },
  profit_ton: {
    id: 'profit_ton',
    name: 'Прибыль (TON)',
    nameEn: 'Profit (TON)',
    icon: '💰',
    color: '#eab308',
    bgColor: 'bg-yellow-500/20',
    borderColor: 'border-yellow-500/50',
    textColor: 'text-yellow-400',
    basePrice: 1.0,
    unit: 'TON',
    tier: 2,
    description: 'Прямая прибыль в TON от Кибер-кафе'
  },
  shares: {
    id: 'shares',
    name: 'Акции',
    nameEn: 'Shares',
    icon: '📈',
    color: '#10b981',
    bgColor: 'bg-emerald-500/20',
    borderColor: 'border-emerald-500/50',
    textColor: 'text-emerald-400',
    basePrice: 0.50,
    unit: 'шт',
    tier: 3,
    description: 'Акции стартапов от Инкубатора'
  },
  ton: {
    id: 'ton',
    name: 'TON',
    nameEn: 'TON',
    icon: '💎',
    color: '#0ea5e9',
    bgColor: 'bg-sky-500/20',
    borderColor: 'border-sky-500/50',
    textColor: 'text-sky-400',
    basePrice: 1.0,
    unit: 'TON',
    tier: 3,
    description: 'Основная валюта TON-City'
  }
};

// Backward compatibility aliases
RESOURCES.food = RESOURCES.biomass;
RESOURCES.algo = RESOURCES.neurocode;
RESOURCES.iron = RESOURCES.repair_kits;

export function getResource(id) {
  return RESOURCES[id] || {
    id,
    name: id,
    nameEn: id,
    icon: '📦',
    color: '#6b7280',
    bgColor: 'bg-gray-500/20',
    borderColor: 'border-gray-500/50',
    textColor: 'text-gray-400',
    basePrice: 0.01,
    unit: 'шт',
    tier: 0,
    description: 'Ресурс'
  };
}

export function getAllResources() {
  return Object.values(RESOURCES).filter(r => !['food', 'algo', 'iron'].includes(r.id));
}

export function formatPrice(price) {
  if (price === undefined || price === null) return '0.00';
  const p = Math.max(0.01, price);
  if (p >= 1) return p.toFixed(2);
  return p.toFixed(3);
}

export function formatAmount(amount) {
  if (!amount) return '0';
  if (amount >= 1000000) return (amount / 1000000).toFixed(1) + 'M';
  if (amount >= 1000) return (amount / 1000).toFixed(1) + 'K';
  return Math.floor(amount).toString();
}

export default RESOURCES;
