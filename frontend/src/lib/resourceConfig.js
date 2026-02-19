/**
 * Resource Configuration with Images
 * All resources in the game with their icons, base prices, and colors
 */

// Resource types from business_config
export const RESOURCES = {
  energy: {
    id: 'energy',
    name: 'Энергия',
    nameEn: 'Energy',
    icon: '⚡',
    color: '#fbbf24', // amber
    bgColor: 'bg-amber-500/20',
    borderColor: 'border-amber-500/50',
    textColor: 'text-amber-400',
    basePrice: 0.01,
    unit: 'кВт',
    description: 'Базовый ресурс для работы всех зданий'
  },
  cu: {
    id: 'cu',
    name: 'Вычислительная мощность',
    nameEn: 'Computing Units',
    icon: '💻',
    color: '#3b82f6', // blue
    bgColor: 'bg-blue-500/20',
    borderColor: 'border-blue-500/50',
    textColor: 'text-blue-400',
    basePrice: 0.02,
    unit: 'TH/s',
    description: 'Для майнинга и вычислений'
  },
  quartz: {
    id: 'quartz',
    name: 'Кварц',
    nameEn: 'Quartz',
    icon: '💎',
    color: '#8b5cf6', // violet
    bgColor: 'bg-violet-500/20',
    borderColor: 'border-violet-500/50',
    textColor: 'text-violet-400',
    basePrice: 0.03,
    unit: 'кг',
    description: 'Редкий минерал для производства чипов'
  },
  traffic: {
    id: 'traffic',
    name: 'Трафик',
    nameEn: 'Traffic',
    icon: '📡',
    color: '#06b6d4', // cyan
    bgColor: 'bg-cyan-500/20',
    borderColor: 'border-cyan-500/50',
    textColor: 'text-cyan-400',
    basePrice: 0.008,
    unit: 'GB',
    description: 'Интернет-трафик для коммуникаций'
  },
  cooling: {
    id: 'cooling',
    name: 'Охлаждение',
    nameEn: 'Cooling',
    icon: '❄️',
    color: '#22d3ee', // cyan-400
    bgColor: 'bg-sky-500/20',
    borderColor: 'border-sky-500/50',
    textColor: 'text-sky-400',
    basePrice: 0.015,
    unit: 'BTU',
    description: 'Для охлаждения серверов и оборудования'
  },
  food: {
    id: 'food',
    name: 'Еда',
    nameEn: 'Food',
    icon: '🌱',
    color: '#22c55e', // green
    bgColor: 'bg-green-500/20',
    borderColor: 'border-green-500/50',
    textColor: 'text-green-400',
    basePrice: 0.005,
    unit: 'кг',
    description: 'Питание для работников'
  },
  scrap: {
    id: 'scrap',
    name: 'Лом',
    nameEn: 'Scrap',
    icon: '♻️',
    color: '#78716c', // stone
    bgColor: 'bg-stone-500/20',
    borderColor: 'border-stone-500/50',
    textColor: 'text-stone-400',
    basePrice: 0.003,
    unit: 'кг',
    description: 'Вторсырье для переработки'
  },
  chips: {
    id: 'chips',
    name: 'Чипы',
    nameEn: 'Chips',
    icon: '🔧',
    color: '#f97316', // orange
    bgColor: 'bg-orange-500/20',
    borderColor: 'border-orange-500/50',
    textColor: 'text-orange-400',
    basePrice: 0.05,
    unit: 'шт',
    description: 'Микросхемы для электроники'
  },
  nft: {
    id: 'nft',
    name: 'NFT Арт',
    nameEn: 'NFT Art',
    icon: '🎨',
    color: '#ec4899', // pink
    bgColor: 'bg-pink-500/20',
    borderColor: 'border-pink-500/50',
    textColor: 'text-pink-400',
    basePrice: 0.10,
    unit: 'шт',
    description: 'Цифровые произведения искусства'
  },
  algo: {
    id: 'algo',
    name: 'Алгоритмы',
    nameEn: 'Algorithms',
    icon: '🧠',
    color: '#a855f7', // purple
    bgColor: 'bg-purple-500/20',
    borderColor: 'border-purple-500/50',
    textColor: 'text-purple-400',
    basePrice: 0.08,
    unit: 'шт',
    description: 'AI алгоритмы и модели'
  },
  logistics: {
    id: 'logistics',
    name: 'Логистика',
    nameEn: 'Logistics',
    icon: '🚁',
    color: '#14b8a6', // teal
    bgColor: 'bg-teal-500/20',
    borderColor: 'border-teal-500/50',
    textColor: 'text-teal-400',
    basePrice: 0.04,
    unit: 'слот',
    description: 'Транспортные услуги'
  },
  iron: {
    id: 'iron',
    name: 'Железо',
    nameEn: 'Iron',
    icon: '🔩',
    color: '#6b7280', // gray
    bgColor: 'bg-gray-500/20',
    borderColor: 'border-gray-500/50',
    textColor: 'text-gray-400',
    basePrice: 0.02,
    unit: 'кг',
    description: 'Металл для строительства'
  }
};

// Get resource by ID
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
    description: 'Неизвестный ресурс'
  };
}

// Get all resources as array
export function getAllResources() {
  return Object.values(RESOURCES);
}

// Format price (max 2 decimals, but keep at least 4 for small prices)
export function formatPrice(price) {
  if (price < 0.01) {
    return price.toFixed(2);
  }
  return Math.round(price * 100) / 100;
}

// Format amount (integer only)
export function formatAmount(amount) {
  return Math.floor(amount);
}

export default RESOURCES;
