"""
TON-City Economic Strategy - Business Configuration V2.0
21 business types across 3 tiers with 10 levels each.
Production growth: +50% per level
Consumption growth: +45% per level
Upgrade cost growth: +60% per level
Durability proportionally affects income (30% quality drop = 30% income drop)
"""

# ==================== TIER TAX RATES ====================
TIER_TAXES = {
    1: 0.15,  # 15% - Basic production
    2: 0.23,  # 23% - Processing
    3: 0.30,  # 30% - Financial/Infrastructure
}

# Turnover tax on every market transaction
TURNOVER_TAX_RATE = 0.02  # 2%

# ==================== PATRON CONFIG ====================
PATRON_TAX_RATE = 0.01  # 1% to patron
INSTANT_WITHDRAWAL_FEE = 0.01  # 1% to bank

PATRON_BONUSES = {
    "gram_bank": {
        "type": "income",
        "multiplier_range": (1.05, 1.25),
    },
    "validator": {
        "type": "production",
        "multiplier_range": (1.10, 1.50),
    },
    "dex": {
        "type": "trade",
        "multiplier_range": (1.05, 1.20),
    },
    "casino": {
        "type": "luck",
        "multiplier_range": (1.01, 1.10),
    },
    "arena": {
        "type": "reputation",
        "multiplier_range": (1.05, 1.15),
    },
    "incubator": {
        "type": "upgrade",
        "multiplier_range": (0.95, 0.80),
    },
    "bridge": {
        "type": "transfer",
        "multiplier_range": (0.98, 0.90),
    },
}

# ==================== MINIMUM PRICE RULE ====================
MIN_PRICE_TON = 0.01  # Nothing in the game can cost less than 0.01 TON

# ==================== RESOURCE TYPES ====================
# ALL base_price values are >= 0.01 TON to enforce minimum price rule
RESOURCE_TYPES = {
    "energy":        {"name_ru": "Энергия",      "name_en": "Energy",       "tier": 1, "icon": "⚡", "base_price": 0.01},
    "cu":            {"name_ru": "Мощность",      "name_en": "Compute",      "tier": 1, "icon": "🖥️", "base_price": 0.02},
    "quartz":        {"name_ru": "Кварц",         "name_en": "Quartz",       "tier": 1, "icon": "💎", "base_price": 0.015},
    "traffic":       {"name_ru": "Трафик",        "name_en": "Traffic",      "tier": 1, "icon": "📡", "base_price": 0.012},
    "cooling":       {"name_ru": "Холод",         "name_en": "Cooling",      "tier": 1, "icon": "❄️", "base_price": 0.02},
    "biomass":       {"name_ru": "Био-масса",     "name_en": "Biomass",      "tier": 1, "icon": "🌿", "base_price": 0.018},
    "scrap":         {"name_ru": "Вторсырье",     "name_en": "Scrap",        "tier": 1, "icon": "🗑️", "base_price": 0.01},
    "chips":         {"name_ru": "Чипы",          "name_en": "Chips",        "tier": 2, "icon": "🔲", "base_price": 0.10},
    "nft":           {"name_ru": "NFT",           "name_en": "NFT",          "tier": 2, "icon": "🎨", "base_price": 0.15},
    "neurocode":     {"name_ru": "Нейро-код",     "name_en": "Neuro-code",   "tier": 2, "icon": "🧠", "base_price": 0.20},
    "logistics":     {"name_ru": "Доставка",      "name_en": "Delivery",     "tier": 2, "icon": "🚚", "base_price": 0.05},
    "profit_ton":    {"name_ru": "Прибыль (TON)", "name_en": "Profit (TON)", "tier": 2, "icon": "💰", "base_price": 1.0},
    "repair_kits":   {"name_ru": "Ремкомплекты",  "name_en": "Repair Kits",  "tier": 2, "icon": "🔧", "base_price": 0.08},
    "vr_experience": {"name_ru": "VR-опыт",       "name_en": "VR Experience","tier": 2, "icon": "🥽", "base_price": 0.12},
    "shares":        {"name_ru": "Акции",         "name_en": "Shares",       "tier": 3, "icon": "📈", "base_price": 0.50},
    "ton":           {"name_ru": "TON",           "name_en": "TON",          "tier": 3, "icon": "💎", "base_price": 1.0},
}

# Resource weights for storage
RESOURCE_WEIGHTS = {
    "energy": 1, "cu": 1, "quartz": 1, "traffic": 1,
    "cooling": 1, "biomass": 1, "scrap": 1,
    "chips": 5, "nft": 10, "neurocode": 10,
    "logistics": 5, "repair_kits": 5, "vr_experience": 5,
    "shares": 20, "profit_ton": 1, "ton": 1,
}

# ==================== NPC PRICE CONTROL ====================
NPC_PRICE_FLOOR = 0.70   # NPC buys if price drops below 70% of base
NPC_PRICE_CEILING = 1.50  # NPC sells if price rises above 150% of base
MONOPOLY_THRESHOLD = 0.40  # 40% market share = double sale tax
MIDNIGHT_DECAY_RATE = 0.10  # 10% inventory loss daily at 00:00 MSK

# ==================== EXACT PRODUCTION/CONSUMPTION DATA ====================
# All values are per-tick (per cycle). Format: {level: value}
# Production grows ~+50% per level, Consumption grows ~+45% per level

BUSINESS_LEVELS = {
    # ===== TIER I: RESOURCE BASE =====
    
    "helios": {
        "production": {1: 100, 2: 150, 3: 225, 4: 338, 5: 506, 6: 759, 7: 1139, 8: 1709, 9: 2563, 10: 3844},
        "consumption": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0},
    },
    "nano_dc": {
        "production": {1: 50, 2: 75, 3: 113, 4: 169, 5: 253, 6: 380, 7: 570, 8: 854, 9: 1282, 10: 1923},
        "consumption": {1: 30, 2: 44, 3: 63, 4: 92, 5: 133, 6: 193, 7: 280, 8: 405, 9: 588, 10: 852},
    },
    "quartz_mine": {
        "production": {1: 80, 2: 120, 3: 180, 4: 270, 5: 405, 6: 608, 7: 911, 8: 1367, 9: 2050, 10: 3075},
        "consumption": {1: 40, 2: 58, 3: 84, 4: 122, 5: 177, 6: 257, 7: 372, 8: 540, 9: 782, 10: 1134},
    },
    "signal_tower": {
        "production": {1: 60, 2: 90, 3: 135, 4: 203, 5: 304, 6: 456, 7: 683, 8: 1025, 9: 1538, 10: 2307},
        "consumption": {1: 25, 2: 36, 3: 53, 4: 76, 5: 111, 6: 160, 7: 233, 8: 337, 9: 489, 10: 709},
    },
    "hydro_cooling": {
        "production": {1: 40, 2: 60, 3: 90, 4: 135, 5: 203, 6: 304, 7: 456, 8: 683, 9: 1025, 10: 1538},
        "consumption": {1: 50, 2: 73, 3: 105, 4: 153, 5: 221, 6: 321, 7: 465, 8: 675, 9: 978, 10: 1418},
    },
    "bio_farm": {
        "production": {1: 70, 2: 105, 3: 158, 4: 236, 5: 354, 6: 532, 7: 797, 8: 1196, 9: 1794, 10: 2691},
        "consumption": {1: 20, 2: 29, 3: 42, 4: 61, 5: 88, 6: 128, 7: 186, 8: 269, 9: 391, 10: 566},
    },
    "scrap_yard": {
        "production": {1: 120, 2: 180, 3: 270, 4: 405, 5: 608, 6: 911, 7: 1367, 8: 2050, 9: 3075, 10: 4613},
        "consumption": {1: 15, 2: 22, 3: 32, 4: 46, 5: 66, 6: 96, 7: 140, 8: 203, 9: 294, 10: 426},
    },
    
    # ===== TIER II: PRODUCTION =====
    
    "chips_factory": {
        "production": {1: 10, 2: 15, 3: 23, 4: 34, 5: 51, 6: 76, 7: 114, 8: 171, 9: 256, 10: 384},
        "consumption": {1: 60, 2: 87, 3: 126, 4: 183, 5: 265, 6: 384, 7: 557, 8: 808, 9: 1171, 10: 1698},
    },
    "nft_studio": {
        "production": {1: 8, 2: 12, 3: 18, 4: 27, 5: 41, 6: 61, 7: 91, 8: 137, 9: 205, 10: 308},
        "consumption": {1: 40, 2: 58, 3: 84, 4: 122, 5: 177, 6: 257, 7: 372, 8: 540, 9: 782, 10: 1134},
    },
    "ai_lab": {
        "production": {1: 5, 2: 8, 3: 11, 4: 17, 5: 25, 6: 38, 7: 57, 8: 85, 9: 128, 10: 192},
        "consumption": {1: 50, 2: 73, 3: 105, 4: 153, 5: 221, 6: 321, 7: 465, 8: 675, 9: 978, 10: 1418},
    },
    "logistics_hub": {
        "production": {1: 25, 2: 38, 3: 56, 4: 84, 5: 127, 6: 190, 7: 285, 8: 427, 9: 641, 10: 962},
        "consumption": {1: 35, 2: 51, 3: 74, 4: 107, 5: 155, 6: 225, 7: 326, 8: 472, 9: 685, 10: 993},
    },
    "cyber_cafe": {
        "production": {1: 120, 2: 180, 3: 270, 4: 405, 5: 608, 6: 911, 7: 1367, 8: 2050, 9: 3075, 10: 4613},
        "consumption": {1: 80, 2: 116, 3: 168, 4: 244, 5: 354, 6: 513, 7: 744, 8: 1078, 9: 1563, 10: 2267},
    },
    "repair_shop": {
        "production": {1: 15, 2: 23, 3: 34, 4: 51, 5: 76, 6: 114, 7: 171, 8: 256, 9: 384, 10: 577},
        "consumption": {1: 70, 2: 102, 3: 147, 4: 214, 5: 310, 6: 449, 7: 651, 8: 944, 9: 1369, 10: 1985},
    },
    "vr_club": {
        "production": {1: 12, 2: 18, 3: 27, 4: 41, 5: 61, 6: 91, 7: 137, 8: 205, 9: 308, 10: 461},
        "consumption": {1: 55, 2: 80, 3: 116, 4: 168, 5: 243, 6: 353, 7: 511, 8: 742, 9: 1075, 10: 1559},
    },
    
    # ===== TIER III: INFRASTRUCTURE (produces TON or Shares) =====
    
    "validator": {
        "production": {1: 500, 2: 750, 3: 1125, 4: 1688, 5: 2531, 6: 3797, 7: 5695, 8: 8543, 9: 12814, 10: 19222},
        "consumption": {1: 350, 2: 508, 3: 736, 4: 1067, 5: 1547, 6: 2244, 7: 3253, 8: 4717, 9: 6840, 10: 9918},
    },
    "gram_bank": {
        "production": {1: 600, 2: 900, 3: 1350, 4: 2025, 5: 3038, 6: 4556, 7: 6834, 8: 10252, 9: 15377, 10: 23066},
        "consumption": {1: 400, 2: 580, 3: 841, 4: 1219, 5: 1768, 6: 2564, 7: 3717, 8: 5390, 9: 7815, 10: 11332},
    },
    "dex": {
        "production": {1: 700, 2: 1050, 3: 1575, 4: 2363, 5: 3544, 6: 5316, 7: 7973, 8: 11960, 9: 17940, 10: 26910},
        "consumption": {1: 500, 2: 725, 3: 1051, 4: 1524, 5: 2210, 6: 3205, 7: 4647, 8: 6738, 9: 9770, 10: 14166},
    },
    "casino": {
        "production": {1: 1000, 2: 1500, 3: 2250, 4: 3375, 5: 5063, 6: 7594, 7: 11391, 8: 17086, 9: 25629, 10: 38443},
        "consumption": {1: 750, 2: 1088, 3: 1577, 4: 2287, 5: 3316, 6: 4808, 7: 6971, 8: 10108, 9: 14657, 10: 21253},
    },
    "arena": {
        "production": {1: 800, 2: 1200, 3: 1800, 4: 2700, 5: 4050, 6: 6075, 7: 9113, 8: 13669, 9: 20503, 10: 30755},
        "consumption": {1: 600, 2: 870, 3: 1262, 4: 1829, 5: 2652, 6: 3846, 7: 5577, 8: 8086, 9: 11725, 10: 17001},
    },
    "incubator": {
        "production": {1: 5, 2: 8, 3: 11, 4: 17, 5: 25, 6: 38, 7: 57, 8: 85, 9: 128, 10: 192},
        "consumption": {1: 150, 2: 218, 3: 315, 4: 457, 5: 663, 6: 962, 7: 1395, 8: 2022, 9: 2932, 10: 4252},
    },
    "bridge": {
        "production": {1: 1500, 2: 2250, 3: 3375, 4: 5063, 5: 7594, 6: 11391, 7: 17086, 8: 25629, 9: 38443, 10: 57665},
        "consumption": {1: 1100, 2: 1595, 3: 2313, 4: 3354, 5: 4863, 6: 7051, 7: 10224, 8: 14825, 9: 21496, 10: 31170},
    },
}


# ==================== BUSINESS DEFINITIONS ====================
BUSINESSES = {
    # ===== TIER I: RESOURCE BASE (consumes Energy) =====
    "helios": {
        "name": {"en": "Helios Solar", "ru": "Солнечная станция"},
        "tier": 1,
        "produces": "energy",
        "consumes": {},  # No consumption, only TON maintenance
        "base_cost_ton": 5,
        "upgrade_requires": "quartz",
        "daily_wear_range": (0.02, 0.03),  # 2-3% daily
        "description": {"en": "Solar power station - produces Energy", "ru": "Солнечная электростанция - производит Энергию"},
        "icon": "☀️",
    },
    "nano_dc": {
        "name": {"en": "Nano DC", "ru": "Дата-центр"},
        "tier": 1,
        "produces": "cu",
        "consumes": {"energy": 1.0},  # 100% consumption goes to energy
        "base_cost_ton": 8,
        "upgrade_requires": "chips",
        "daily_wear_range": (0.03, 0.04),
        "description": {"en": "Data center - produces Compute Power", "ru": "Дата-центр - производит Мощность"},
        "icon": "🖥️",
    },
    "quartz_mine": {
        "name": {"en": "Quartz Mine", "ru": "Шахта Кварца"},
        "tier": 1,
        "produces": "quartz",
        "consumes": {"energy": 1.0},
        "base_cost_ton": 6,
        "upgrade_requires": "chips",
        "daily_wear_range": (0.04, 0.05),
        "description": {"en": "Quartz crystal mining", "ru": "Добыча кварца"},
        "icon": "💎",
    },
    "signal_tower": {
        "name": {"en": "Signal Tower", "ru": "Вышка Трафика"},
        "tier": 1,
        "produces": "traffic",
        "consumes": {"energy": 1.0},
        "base_cost_ton": 4,
        "upgrade_requires": "chips",
        "daily_wear_range": (0.02, 0.03),
        "description": {"en": "Network traffic provider", "ru": "Провайдер сетевого трафика"},
        "icon": "📡",
    },
    "hydro_cooling": {
        "name": {"en": "Cooler", "ru": "Хладокомбинат"},
        "tier": 1,
        "produces": "cooling",
        "consumes": {"energy": 1.0},
        "base_cost_ton": 5,
        "upgrade_requires": "chips",
        "daily_wear_range": (0.02, 0.04),
        "description": {"en": "Cooling systems", "ru": "Системы охлаждения"},
        "icon": "❄️",
    },
    "bio_farm": {
        "name": {"en": "Bio Farm", "ru": "Био-ферма"},
        "tier": 1,
        "produces": "biomass",
        "consumes": {"energy": 1.0},
        "base_cost_ton": 4,
        "upgrade_requires": "quartz",
        "daily_wear_range": (0.03, 0.04),
        "description": {"en": "Organic biomass production", "ru": "Производство био-массы"},
        "icon": "🌿",
    },
    "scrap_yard": {
        "name": {"en": "Scrap Yard", "ru": "Свалка"},
        "tier": 1,
        "produces": "scrap",
        "consumes": {"energy": 1.0},
        "base_cost_ton": 3,
        "upgrade_requires": None,
        "daily_wear_range": (0.02, 0.03),
        "description": {"en": "Scrap collection", "ru": "Сбор вторсырья"},
        "icon": "🗑️",
    },
    
    # ===== TIER II: PRODUCTION (consumes Tier 1 resources) =====
    "chips_factory": {
        "name": {"en": "Chips Factory", "ru": "Завод Микросхем"},
        "tier": 2,
        "produces": "chips",
        "consumes": {"quartz": 0.5, "cooling": 0.5},  # Split 50/50
        "base_cost_ton": 15,
        "upgrade_requires": "neurocode",
        "daily_wear_range": (0.04, 0.05),
        "description": {"en": "Microchip manufacturing", "ru": "Производство микросхем"},
        "icon": "🔲",
    },
    "nft_studio": {
        "name": {"en": "NFT Studio", "ru": "NFT-Студия"},
        "tier": 2,
        "produces": "nft",
        "consumes": {"cu": 0.5, "traffic": 0.5},
        "base_cost_ton": 20,
        "upgrade_requires": "neurocode",
        "daily_wear_range": (0.03, 0.04),
        "description": {"en": "NFT creation studio", "ru": "Студия создания NFT"},
        "icon": "🎨",
    },
    "ai_lab": {
        "name": {"en": "AI Lab", "ru": "Лаборатория ИИ"},
        "tier": 2,
        "produces": "neurocode",
        "consumes": {"cu": 0.5, "energy": 0.5},
        "base_cost_ton": 25,
        "upgrade_requires": "nft",
        "daily_wear_range": (0.04, 0.06),
        "description": {"en": "AI neuro-code development", "ru": "Разработка нейро-кода"},
        "icon": "🤖",
    },
    "logistics_hub": {
        "name": {"en": "Logistics Hub", "ru": "Логистический Ангар"},
        "tier": 2,
        "produces": "logistics",
        "consumes": {"traffic": 0.5, "energy": 0.5},
        "base_cost_ton": 12,
        "upgrade_requires": "chips",
        "daily_wear_range": (0.02, 0.04),
        "description": {"en": "Goods transportation", "ru": "Транспортировка товаров"},
        "icon": "🚚",
    },
    "cyber_cafe": {
        "name": {"en": "Cyber Cafe", "ru": "Кибер-кафе"},
        "tier": 2,
        "produces": "profit_ton",  # Direct TON profit
        "consumes": {"biomass": 0.5, "energy": 0.5},
        "base_cost_ton": 10,
        "upgrade_requires": "chips",
        "daily_wear_range": (0.02, 0.04),
        "description": {"en": "Gaming and food spot - direct TON income", "ru": "Кибер-кафе - прямая прибыль в TON"},
        "icon": "☕",
    },
    "repair_shop": {
        "name": {"en": "Repair Shop", "ru": "Ремзона"},
        "tier": 2,
        "produces": "repair_kits",
        "consumes": {"scrap": 0.5, "chips": 0.5},
        "base_cost_ton": 8,
        "upgrade_requires": "chips",
        "daily_wear_range": (0.03, 0.04),
        "description": {"en": "Repair kits production", "ru": "Производство ремкомплектов"},
        "icon": "🔧",
    },
    "vr_club": {
        "name": {"en": "VR Club", "ru": "VR-Клуб"},
        "tier": 2,
        "produces": "vr_experience",
        "consumes": {"traffic": 0.5, "chips": 0.5},
        "base_cost_ton": 18,
        "upgrade_requires": "nft",
        "daily_wear_range": (0.04, 0.05),
        "description": {"en": "Virtual reality entertainment", "ru": "VR развлечения"},
        "icon": "🥽",
    },
    
    # ===== TIER III: INFRASTRUCTURE (produces TON / Shares) =====
    "validator": {
        "name": {"en": "Validator Node", "ru": "Валидатор"},
        "tier": 3,
        "produces": "ton",
        "consumes": {"neurocode": 0.5, "cu": 0.5},
        "base_cost_ton": 50,
        "upgrade_requires": "chips",
        "daily_wear_range": (0.05, 0.07),
        "description": {"en": "Blockchain validator - produces TON", "ru": "Валидатор блокчейна - производит TON"},
        "icon": "⚡",
        "is_patron": True,
        "patron_type": "validator",
    },
    "gram_bank": {
        "name": {"en": "Gram Bank", "ru": "Банк Gram"},
        "tier": 3,
        "produces": "ton",
        "consumes": {"traffic": 0.5, "nft": 0.5},
        "base_cost_ton": 60,
        "upgrade_requires": "neurocode",
        "daily_wear_range": (0.03, 0.05),
        "description": {"en": "Banking services - produces TON", "ru": "Банковские услуги - производит TON"},
        "icon": "🏦",
        "is_patron": True,
        "patron_type": "gram_bank",
        "instant_withdrawal": True,
    },
    "dex": {
        "name": {"en": "DEX Exchange", "ru": "Биржа (DEX)"},
        "tier": 3,
        "produces": "ton",
        "consumes": {"traffic": 0.5, "neurocode": 0.5},
        "base_cost_ton": 55,
        "upgrade_requires": "nft",
        "daily_wear_range": (0.04, 0.05),
        "description": {"en": "Decentralized exchange - produces TON", "ru": "Децентрализованная биржа - производит TON"},
        "icon": "📊",
        "is_patron": True,
        "patron_type": "dex",
    },
    "casino": {
        "name": {"en": "Crypto Casino", "ru": "Казино"},
        "tier": 3,
        "produces": "ton",
        "consumes": {"vr_experience": 0.5, "traffic": 0.5},
        "base_cost_ton": 70,
        "upgrade_requires": "neurocode",
        "daily_wear_range": (0.04, 0.06),
        "description": {"en": "Gambling entertainment - produces TON", "ru": "Азартные игры - производит TON"},
        "icon": "🎰",
        "is_patron": True,
        "patron_type": "casino",
    },
    "arena": {
        "name": {"en": "Battle Arena", "ru": "Арена"},
        "tier": 3,
        "produces": "ton",
        "consumes": {"vr_experience": 0.5, "biomass": 0.5},
        "base_cost_ton": 45,
        "upgrade_requires": "nft",
        "daily_wear_range": (0.04, 0.05),
        "description": {"en": "PvP competitions - produces TON", "ru": "PvP соревнования - производит TON"},
        "icon": "⚔️",
        "is_patron": True,
        "patron_type": "arena",
    },
    "incubator": {
        "name": {"en": "Startup Incubator", "ru": "Инкубатор"},
        "tier": 3,
        "produces": "shares",
        "consumes": {"biomass": 0.5, "neurocode": 0.5},
        "base_cost_ton": 40,
        "upgrade_requires": "nft",
        "daily_wear_range": (0.02, 0.04),
        "description": {"en": "Startup incubator - produces Shares", "ru": "Инкубатор стартапов - производит Акции"},
        "icon": "🚀",
        "is_patron": True,
        "patron_type": "incubator",
    },
    "bridge": {
        "name": {"en": "Cross-Chain Bridge", "ru": "Мост (Bridge)"},
        "tier": 3,
        "produces": "ton",
        "consumes": {"energy": 0.5, "chips": 0.5},
        "base_cost_ton": 48,
        "upgrade_requires": "chips",
        "daily_wear_range": (0.03, 0.05),
        "description": {"en": "Cross-chain bridge - produces TON", "ru": "Кросс-чейн мост - производит TON"},
        "icon": "🌉",
        "is_patron": True,
        "patron_type": "bridge",
    },
}


# ==================== UPGRADE COSTS ====================
UPGRADE_COST_MULTIPLIER = 1.60  # +60% per level

# Maintenance costs by tier and level (daily TON cost)
MAINTENANCE_COSTS = {
    1: {1: 0.05, 2: 0.08, 3: 0.12, 4: 0.18, 5: 0.25, 6: 0.35, 7: 0.48, 8: 0.65, 9: 0.85, 10: 1.10},
    2: {1: 0.50, 2: 0.80, 3: 1.20, 4: 1.80, 5: 2.50, 6: 3.50, 7: 4.80, 8: 6.50, 9: 8.50, 10: 11.00},
    3: {1: 5.00, 2: 8.00, 3: 12.00, 4: 18.00, 5: 25.00, 6: 35.00, 7: 48.00, 8: 65.00, 9: 85.00, 10: 120.00},
}


# ==================== ESTIMATED DAILY NET INCOME (TON) ====================
# Guaranteed profitable: Tier 1 < Tier 2 < Tier 3
# Growth ×1.5 per level (matches production growth)
# These represent NET income after all costs (resources, tax, maintenance)
# with 100% durability and NO patron bonus

def _gen_income(base, levels=10):
    """Generate income table: base × 1.5^(level-1)"""
    return {lv: round(base * (1.5 ** (lv - 1)), 2) for lv in range(1, levels + 1)}

ESTIMATED_DAILY_INCOME = {
    # Tier 1: 0.5 - 1.5 TON/day at L1
    "helios":        _gen_income(1.00),
    "nano_dc":       _gen_income(0.85),
    "quartz_mine":   _gen_income(0.90),
    "signal_tower":  _gen_income(0.70),
    "hydro_cooling": _gen_income(0.60),
    "bio_farm":      _gen_income(0.80),
    "scrap_yard":    _gen_income(0.75),
    # Tier 2: 2 - 5 TON/day at L1
    "chips_factory": _gen_income(3.00),
    "nft_studio":    _gen_income(3.50),
    "ai_lab":        _gen_income(4.00),
    "logistics_hub": _gen_income(2.50),
    "cyber_cafe":    _gen_income(3.00),
    "repair_shop":   _gen_income(2.80),
    "vr_club":       _gen_income(3.50),
    # Tier 3: 8 - 25 TON/day at L1
    "validator":     _gen_income(10.0),
    "gram_bank":     _gen_income(12.0),
    "dex":           _gen_income(14.0),
    "casino":        _gen_income(20.0),
    "arena":         _gen_income(16.0),
    "incubator":     _gen_income(8.0),
    "bridge":        _gen_income(25.0),
}


# ==================== PATRONAGE BONUSES V2 ====================
# Tier 3 businesses provide bonuses to Tier 1 and 2 businesses
# Each patron type gives specific benefits to "child" businesses

PATRONAGE_EFFECTS = {
    "validator": {
        "name_ru": "Валидатор",
        "bonus_type": "production",
        "bonus_per_level": 0.03,     # +3% per patron level to production
        "max_bonus": 0.30,           # max +30% at patron L10
        "applies_to_tiers": [1, 2],  # Boosts all Tier 1 and 2
        "special": "Увеличивает производство подопечных бизнесов",
    },
    "gram_bank": {
        "name_ru": "Банк Gram",
        "bonus_type": "income",
        "bonus_per_level": 0.025,    # +2.5% per level to income
        "max_bonus": 0.25,
        "applies_to_tiers": [1, 2],
        "special": "Увеличивает доход подопечных бизнесов, мгновенный вывод",
    },
    "dex": {
        "name_ru": "Биржа DEX",
        "bonus_type": "trade",
        "bonus_per_level": 0.02,     # -2% per level on trade fees
        "max_bonus": 0.20,
        "applies_to_tiers": [1, 2],
        "special": "Снижает комиссию на торговлю для подопечных",
    },
    "casino": {
        "name_ru": "Казино",
        "bonus_type": "luck",
        "bonus_per_level": 0.01,     # +1% per level random bonus income
        "max_bonus": 0.10,
        "applies_to_tiers": [1, 2],
        "special": "Случайный бонус к доходу подопечных",
    },
    "arena": {
        "name_ru": "Арена",
        "bonus_type": "durability",
        "bonus_per_level": 0.02,     # -2% per level durability loss
        "max_bonus": 0.20,
        "applies_to_tiers": [1, 2],
        "special": "Снижает износ зданий подопечных",
    },
    "incubator": {
        "name_ru": "Инкубатор",
        "bonus_type": "upgrade_discount",
        "bonus_per_level": 0.03,     # -3% per level upgrade cost
        "max_bonus": 0.30,
        "applies_to_tiers": [1, 2],
        "special": "Снижает стоимость улучшений подопечных",
    },
    "bridge": {
        "name_ru": "Мост",
        "bonus_type": "transfer",
        "bonus_per_level": 0.015,    # -1.5% per level withdrawal fee
        "max_bonus": 0.15,
        "applies_to_tiers": [1, 2],
        "special": "Снижает комиссию на вывод для подопечных",
    },
}


def get_estimated_daily_income(business_type: str, level: int, durability: float = 100.0, patron_bonus: float = 0.0) -> float:
    """Get estimated daily net income in TON for a business"""
    incomes = ESTIMATED_DAILY_INCOME.get(business_type, {})
    base = incomes.get(level, incomes.get(1, 0))
    durability_mult = durability / 100.0
    return round(base * durability_mult * (1 + patron_bonus), 4)


def get_patron_effect(patron_type: str, patron_level: int) -> dict:
    """Get detailed patron bonus for a Tier 3 business"""
    effect = PATRONAGE_EFFECTS.get(patron_type, {})
    if not effect:
        return {"bonus": 0, "type": "none", "description": ""}
    bonus = min(effect["bonus_per_level"] * patron_level, effect["max_bonus"])
    return {
        "bonus": round(bonus, 4),
        "type": effect["bonus_type"],
        "max_bonus": effect["max_bonus"],
        "description": effect.get("special", ""),
        "applies_to": effect.get("applies_to_tiers", []),
    }


# ==================== WAREHOUSE CONFIG ====================
WAREHOUSE_CONFIG = {
    "base_capacity_multiplier": 3,  # Base storage = daily production × 3
    "overflow_stops_production": True,
    "expansion_slots": {
        1: {"unlock_level": 3, "capacity_days": 1.0},    # +1 day production
        2: {"unlock_level": 7, "capacity_days": 1.5},    # +1.5 days
        3: {"unlock_level": 10, "capacity_days": 2.0},   # +2 days
    },
    "slot_upgrade_costs": {
        1: {"scrap": 50, "energy": 100},                  # Tier 1
        2: {"scrap": 100, "repair_kits": 20},             # Tier 2
        3: {"scrap": 200, "chips": 30, "logistics": 50},  # Tier 3
    },
    "rental_tax_rate": 0.15,
}

# ROI estimates (days)
ROI_ESTIMATES = {
    1: (12, 18),   # Tier 1: 12-18 days
    2: (20, 30),   # Tier 2: 20-30 days
    3: (35, 50),   # Tier 3: 35-50 days
}


# ==================== HELPER FUNCTIONS ====================

def get_production(business_type: str, level: int) -> int:
    """Get exact production value for business at given level"""
    levels = BUSINESS_LEVELS.get(business_type, {})
    prod = levels.get("production", {})
    return prod.get(level, prod.get(1, 0))


def get_consumption(business_type: str, level: int) -> int:
    """Get total consumption value for business at given level"""
    levels = BUSINESS_LEVELS.get(business_type, {})
    cons = levels.get("consumption", {})
    return cons.get(level, cons.get(1, 0))


def get_consumption_breakdown(business_type: str, level: int) -> dict:
    """
    Get per-resource consumption breakdown.
    Total consumption is split according to consumes ratios.
    Returns: {resource_name: amount}
    """
    config = BUSINESSES.get(business_type)
    if not config:
        return {}
    
    total_consumption = get_consumption(business_type, level)
    if total_consumption == 0:
        return {}
    
    consumes = config.get("consumes", {})
    if not consumes:
        return {}
    
    breakdown = {}
    for resource, ratio in consumes.items():
        breakdown[resource] = int(total_consumption * ratio)
    
    return breakdown


def calculate_effective_production(business_type: str, level: int, durability: float, patron_bonus: float = 1.0) -> float:
    """
    Calculate production with durability modifier.
    RULE: If quality drops by X%, income drops by X%.
    durability is 0-100 float.
    """
    base = get_production(business_type, level)
    durability_mult = durability / 100.0
    return base * durability_mult * patron_bonus


def calculate_effective_income(business_type: str, level: int, durability: float, patron_bonus: float = 1.0) -> float:
    """
    Calculate income with durability modifier.
    For Tier 3 TON producers: production value IS the income in internal units.
    Durability proportionally affects income.
    """
    production = calculate_effective_production(business_type, level, durability, patron_bonus)
    return production


def calculate_upgrade_cost(business_type: str, current_level: int) -> dict:
    """Calculate upgrade cost for next level"""
    config = BUSINESSES.get(business_type)
    if not config:
        return None
    
    base_ton = config["base_cost_ton"]
    upgrade_resource = config.get("upgrade_requires")
    
    multiplier = UPGRADE_COST_MULTIPLIER ** current_level
    
    ton_cost = base_ton * multiplier
    resource_cost = int(10 * multiplier) if upgrade_resource else 0
    
    return {
        "ton": round(ton_cost, 2),
        "resource_type": upgrade_resource,
        "resource_amount": resource_cost,
    }


def get_daily_wear(business_type: str, level: int) -> float:
    """Get daily wear percentage (as decimal, e.g. 0.03 = 3%)"""
    config = BUSINESSES.get(business_type)
    if not config:
        return 0.05
    
    min_wear, max_wear = config.get("daily_wear_range", (0.03, 0.05))
    # Higher levels have slightly more wear
    level_factor = (level - 1) / 9.0  # 0 to 1
    wear = min_wear + (max_wear - min_wear) * level_factor
    return min(wear, 0.10)  # Cap at 10%


def calculate_repair_cost(business_type: str, level: int, missing_durability: float) -> dict:
    """
    Calculate repair cost. Requires Repair Kits + TON.
    missing_durability: 0-100 (how much to repair)
    """
    config = BUSINESSES.get(business_type)
    if not config:
        return {"ton": 0, "repair_kits": 0}
    
    tier = config.get("tier", 1)
    maintenance = MAINTENANCE_COSTS.get(tier, {}).get(level, 0.05)
    
    # Repair cost = maintenance * (missing% / 100)
    ton_cost = maintenance * (missing_durability / 100.0)
    
    # Repair kits needed: scales with level and tier
    kits_needed = max(1, int(level * tier * (missing_durability / 100.0)))
    
    return {
        "ton": round(ton_cost, 4),
        "repair_kits": kits_needed,
    }


def get_storage_capacity(business_type: str, level: int) -> int:
    """Calculate built-in storage capacity = daily production × 3"""
    production = get_production(business_type, level)
    return int(production * WAREHOUSE_CONFIG["base_capacity_multiplier"])


def get_expansion_slot_capacity(business_type: str, level: int, slot_number: int) -> int:
    """Get extra capacity from expansion slot"""
    slot_config = WAREHOUSE_CONFIG["expansion_slots"].get(slot_number)
    if not slot_config:
        return 0
    if level < slot_config["unlock_level"]:
        return 0
    
    production = get_production(business_type, level)
    return int(production * slot_config["capacity_days"])


def get_patron_bonus(patron_type: str, patron_level: int, bonus_type: str) -> float:
    """Calculate patron bonus multiplier"""
    patron_config = PATRON_BONUSES.get(patron_type)
    if not patron_config or patron_config["type"] != bonus_type:
        return 1.0
    
    min_mult, max_mult = patron_config["multiplier_range"]
    progress = (patron_level - 1) / 9.0
    
    if bonus_type in ["upgrade", "transfer"]:
        return max_mult + (min_mult - max_mult) * (1 - progress)
    else:
        return min_mult + (max_mult - min_mult) * progress


def check_resource_requirements(business_type: str, level: int, available_resources: dict) -> dict:
    """
    Check if business has enough resources to operate for one tick.
    Returns dict with status and missing resources.
    """
    breakdown = get_consumption_breakdown(business_type, level)
    if not breakdown:
        return {"can_operate": True, "missing": [], "reason": None}
    
    missing = []
    for resource, required in breakdown.items():
        available = available_resources.get(resource, 0)
        if available < required:
            missing.append({
                "resource": resource,
                "required": required,
                "available": available,
                "deficit": required - available,
            })
    
    return {
        "can_operate": len(missing) == 0,
        "missing": missing,
        "reason": "missing_resources" if missing else None,
    }


def get_business_full_stats(business_type: str, level: int = 1, durability: float = 100.0) -> dict:
    """
    Get complete stats for a business at a specific level.
    """
    config = BUSINESSES.get(business_type)
    if not config:
        return None
    
    tier = config.get("tier", 1)
    tax_rate = TIER_TAXES.get(tier, 0.15)
    
    raw_production = get_production(business_type, level)
    effective_production = calculate_effective_production(business_type, level, durability)
    total_consumption = get_consumption(business_type, level)
    consumption_breakdown = get_consumption_breakdown(business_type, level)
    
    maintenance = MAINTENANCE_COSTS.get(tier, {}).get(level, 0.05)
    storage = get_storage_capacity(business_type, level)
    
    # Upgrade cost
    upgrade_cost = calculate_upgrade_cost(business_type, level) if level < 10 else None
    
    return {
        "business_type": business_type,
        "name": config.get("name", {}),
        "tier": tier,
        "level": level,
        "max_level": 10,
        "icon": config.get("icon", "🏢"),
        "produces": config.get("produces"),
        "production": {
            "raw": raw_production,
            "effective": round(effective_production, 2),
            "durability_modifier": round(durability / 100.0, 2),
        },
        "consumption": {
            "total": total_consumption,
            "breakdown": consumption_breakdown,
        },
        "net_output": round(effective_production - total_consumption * (durability / 100.0), 2),
        "taxes": {
            "income_tax_rate": tax_rate,
            "turnover_tax_rate": TURNOVER_TAX_RATE,
        },
        "costs": {
            "maintenance_daily_ton": maintenance,
            "upgrade": upgrade_cost,
        },
        "storage_capacity": storage,
        "durability": durability,
        "daily_wear": get_daily_wear(business_type, level),
        "description": config.get("description", {}),
    }


def get_all_businesses_summary() -> dict:
    """Get summary of all 21 businesses at all 10 levels."""
    result = {}
    for biz_type in BUSINESSES.keys():
        result[biz_type] = {}
        for level in range(1, 11):
            result[biz_type][level] = get_business_full_stats(biz_type, level)
    return result
