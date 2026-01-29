// Building sprites configuration for TON City Builder
export const BUILDING_SPRITES = {
  farm: {
    url: "https://static.prod-images.emergentagent.com/jobs/6fe94a46-7a58-4488-b642-1de98bdc5ebc/images/13db0cc45704f3b4e57a597192ffa72e7624887cc4e793fe75f63f4a6b316605.png",
    name: { en: "Farm", ru: "Ферма" },
    icon: "🌾"
  },
  power_plant: {
    url: "https://static.prod-images.emergentagent.com/jobs/6fe94a46-7a58-4488-b642-1de98bdc5ebc/images/99d80a5156b8df6da8082d47065bcd035c5ad10cb043efd26d5b3f410ae942cc.png",
    name: { en: "Power Plant", ru: "Электростанция" },
    icon: "⚡"
  },
  quarry: {
    url: "https://static.prod-images.emergentagent.com/jobs/6fe94a46-7a58-4488-b642-1de98bdc5ebc/images/b42476718ce3bdd094f31357250e863fef597aa79d3808f1c580c251d3cd49b1.png",
    name: { en: "Quarry", ru: "Карьер" },
    icon: "⛏️"
  },
  factory: {
    url: "https://static.prod-images.emergentagent.com/jobs/6fe94a46-7a58-4488-b642-1de98bdc5ebc/images/463061daaf5519a6020cad6dcf37d5c288bcb8d06238fb861cc2aa6a1aed534a.png",
    name: { en: "Factory", ru: "Завод" },
    icon: "🏭"
  },
  shop: {
    url: "https://static.prod-images.emergentagent.com/jobs/6fe94a46-7a58-4488-b642-1de98bdc5ebc/images/f1115e7e8d7ba2df498a7453abf5817e5596d4d49b6f672189fad90d3ed0ac96.png",
    name: { en: "Shop", ru: "Магазин" },
    icon: "🏪"
  },
  restaurant: {
    url: "https://static.prod-images.emergentagent.com/jobs/6fe94a46-7a58-4488-b642-1de98bdc5ebc/images/49f1125af99a740fb12813afcee7cc9503383b3290ce428df024843b32f1bc4f.png",
    name: { en: "Restaurant", ru: "Ресторан" },
    icon: "🍽️"
  },
  bank: {
    url: "https://static.prod-images.emergentagent.com/jobs/6fe94a46-7a58-4488-b642-1de98bdc5ebc/images/2dd3bc2c848b0794067c62ae95667d9b98b021c2c4103730944e83bc24608fec.png",
    name: { en: "Bank", ru: "Банк" },
    icon: "🏦"
  }
};

// Business types with costs and production
export const BUSINESS_CONFIG = {
  farm: {
    cost: 5,
    buildTime: 2, // hours
    produces: "crops",
    productionRate: 100,
    baseIncome: 2.4,
    operatingCost: 0.3
  },
  power_plant: {
    cost: 20,
    buildTime: 8,
    produces: "energy",
    productionRate: 500,
    baseIncome: 2.4,
    operatingCost: 0.8
  },
  quarry: {
    cost: 25,
    buildTime: 10,
    produces: "materials",
    productionRate: 50,
    baseIncome: 6.0,
    operatingCost: 1.5
  },
  factory: {
    cost: 15,
    buildTime: 6,
    produces: "goods",
    productionRate: 30,
    baseIncome: 2.88,
    operatingCost: 1.44
  },
  shop: {
    cost: 10,
    buildTime: 4,
    produces: "retail",
    productionRate: 0,
    baseIncome: 4.8,
    operatingCost: 0.5
  },
  restaurant: {
    cost: 12,
    buildTime: 5,
    produces: "food_service",
    productionRate: 30,
    baseIncome: 5.4,
    operatingCost: 0.86
  },
  bank: {
    cost: 50,
    buildTime: 24,
    produces: "finance",
    productionRate: 0,
    baseIncome: 4.5,
    operatingCost: 0.6
  }
};
