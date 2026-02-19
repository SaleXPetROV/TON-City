"""
TON Island Economic Strategy - Business Configuration
21 business types across 3 tiers with 10 levels each
"""

# Tier Tax Rates
TIER_TAXES = {
    1: 0.15,  # 15% - Basic production
    2: 0.23,  # 23% - Processing
    3: 0.30,  # 30% - Financial/Entertainment
}

# Patron bonuses
PATRON_BONUSES = {
    "gram_bank": {
        "type": "income",
        "multiplier_range": (1.05, 1.25),  # 5-25% income boost based on bank level
    },
    "validator": {
        "type": "production",
        "multiplier_range": (1.10, 1.50),  # 10-50% production boost based on validator level
    },
    "dex": {
        "type": "trade",
        "multiplier_range": (1.05, 1.20),  # 5-20% better trade prices
    },
    "casino": {
        "type": "luck",
        "multiplier_range": (1.01, 1.10),  # Random bonus events
    },
    "arena": {
        "type": "reputation",
        "multiplier_range": (1.05, 1.15),  # Reputation gain boost
    },
    "incubator": {
        "type": "upgrade",
        "multiplier_range": (0.95, 0.80),  # Upgrade cost reduction (lower is better)
    },
    "bridge": {
        "type": "transfer",
        "multiplier_range": (0.98, 0.90),  # Transfer fee reduction
    },
}

# Resource types and weights
RESOURCE_WEIGHTS = {
    "energy": 1,      # Simple
    "traffic": 1,     # Simple
    "cu": 1,          # Simple (Compute Units)
    "cooling": 1,     # Simple
    "iron": 3,        # Material
    "quartz": 3,      # Material
    "food": 3,        # Material
    "scrap": 3,       # Material
    "chips": 5,       # Processed
    "nft": 10,        # Complex
    "algo": 10,       # Complex
    "logistics": 5,   # Service
}

# Business configurations
BUSINESSES = {
    # ===== TIER I (15% tax) - Basic Production =====
    "helios": {
        "name": {"en": "Helios Solar", "ru": "Гелиос Солар"},
        "tier": 1,
        "produces": "energy",
        "consumes": [],
        "base_production": 100,
        "base_income": 0,
        "base_cost_ton": 5,
        "base_cost_resource": None,
        "upgrade_requires": "quartz",  # Needs quartz for solar panels
        "daily_wear": 0.03,  # 3% daily wear
        "description": {"en": "Solar power station", "ru": "Солнечная электростанция"},
        "icon": "☀️",
    },
    "nano_dc": {
        "name": {"en": "Nano DC", "ru": "Нано ДЦ"},
        "tier": 1,
        "produces": "cu",
        "consumes": ["energy"],
        "base_production": 50,
        "base_income": 0,
        "base_cost_ton": 8,
        "base_cost_resource": "energy",
        "upgrade_requires": "chips",
        "daily_wear": 0.04,
        "description": {"en": "Data center for compute", "ru": "Дата-центр вычислений"},
        "icon": "🖥️",
    },
    "quartz_mine": {
        "name": {"en": "Quartz Mine", "ru": "Кварцевая шахта"},
        "tier": 1,
        "produces": "quartz",
        "consumes": ["energy"],
        "base_production": 30,
        "base_income": 0,
        "base_cost_ton": 6,
        "base_cost_resource": None,
        "upgrade_requires": "iron",
        "daily_wear": 0.05,
        "description": {"en": "Quartz crystal mining", "ru": "Добыча кварца"},
        "icon": "💎",
    },
    "signal_tower": {
        "name": {"en": "Signal Tower", "ru": "Сигнальная башня"},
        "tier": 1,
        "produces": "traffic",
        "consumes": ["energy"],
        "base_production": 200,
        "base_income": 0,
        "base_cost_ton": 4,
        "base_cost_resource": None,
        "upgrade_requires": "chips",
        "daily_wear": 0.02,
        "description": {"en": "Network traffic provider", "ru": "Провайдер сетевого трафика"},
        "icon": "📡",
    },
    "hydro_cooling": {
        "name": {"en": "Hydro Cooling", "ru": "Гидро охлаждение"},
        "tier": 1,
        "produces": "cooling",
        "consumes": ["energy"],
        "base_production": 80,
        "base_income": 0,
        "base_cost_ton": 5,
        "base_cost_resource": None,
        "upgrade_requires": "iron",
        "daily_wear": 0.03,
        "description": {"en": "Cooling systems", "ru": "Системы охлаждения"},
        "icon": "❄️",
    },
    "bio_food": {
        "name": {"en": "BioFood Farm", "ru": "БиоФуд ферма"},
        "tier": 1,
        "produces": "food",
        "consumes": ["energy"],
        "base_production": 60,
        "base_income": 0,
        "base_cost_ton": 4,
        "base_cost_resource": None,
        "upgrade_requires": "quartz",
        "daily_wear": 0.04,
        "description": {"en": "Organic food production", "ru": "Органическое производство еды"},
        "icon": "🌿",
    },
    "scrap_yard": {
        "name": {"en": "Scrap Yard", "ru": "Свалка"},
        "tier": 1,
        "produces": "scrap",
        "consumes": [],
        "base_production": 40,
        "base_income": 0,
        "base_cost_ton": 3,
        "base_cost_resource": None,
        "upgrade_requires": None,
        "daily_wear": 0.02,
        "description": {"en": "Scrap metal collection", "ru": "Сбор металлолома"},
        "icon": "🗑️",
    },
    
    # ===== TIER II (23% tax) - Processing =====
    "chips_factory": {
        "name": {"en": "Chips Factory", "ru": "Завод чипов"},
        "tier": 2,
        "produces": "chips",
        "consumes": ["quartz", "iron", "energy"],
        "base_production": 20,
        "base_income": 0,
        "base_cost_ton": 15,
        "base_cost_resource": "quartz",
        "upgrade_requires": "algo",
        "daily_wear": 0.05,
        "description": {"en": "Microchip manufacturing", "ru": "Производство микрочипов"},
        "icon": "🔲",
    },
    "nft_studio": {
        "name": {"en": "NFT Studio", "ru": "NFT Студия"},
        "tier": 2,
        "produces": "nft",
        "consumes": ["cu", "traffic"],
        "base_production": 10,
        "base_income": 0,
        "base_cost_ton": 20,
        "base_cost_resource": "cu",
        "upgrade_requires": "algo",
        "daily_wear": 0.04,
        "description": {"en": "NFT creation studio", "ru": "Студия создания NFT"},
        "icon": "🎨",
    },
    "ai_lab": {
        "name": {"en": "AI Lab", "ru": "AI Лаборатория"},
        "tier": 2,
        "produces": "algo",
        "consumes": ["cu", "cooling", "energy"],
        "base_production": 15,
        "base_income": 0,
        "base_cost_ton": 25,
        "base_cost_resource": "chips",
        "upgrade_requires": "nft",
        "daily_wear": 0.06,
        "description": {"en": "AI algorithm development", "ru": "Разработка AI алгоритмов"},
        "icon": "🤖",
    },
    "logistics_hub": {
        "name": {"en": "Logistics Hub", "ru": "Логистический хаб"},
        "tier": 2,
        "produces": "logistics",
        "consumes": ["energy", "traffic"],
        "base_production": 50,
        "base_income": 0,
        "base_cost_ton": 12,
        "base_cost_resource": "scrap",
        "upgrade_requires": "iron",
        "daily_wear": 0.03,
        "description": {"en": "Goods transportation", "ru": "Транспортировка товаров"},
        "icon": "🚚",
    },
    "cyber_cafe": {
        "name": {"en": "Cyber Cafe", "ru": "Кибер кафе"},
        "tier": 2,
        "produces": None,  # Service - generates income from traffic
        "consumes": ["food", "traffic", "energy"],
        "base_production": 0,
        "base_income": 0,
        "base_cost_ton": 10,
        "base_cost_resource": "food",
        "upgrade_requires": "chips",
        "daily_wear": 0.03,
        "description": {"en": "Gaming and food spot", "ru": "Игровое и еда"},
        "icon": "☕",
    },
    "repair_shop": {
        "name": {"en": "Repair Shop", "ru": "Ремонтная мастерская"},
        "tier": 2,
        "produces": "iron",  # Recycles scrap to iron
        "consumes": ["scrap", "energy"],
        "base_production": 25,
        "base_income": 0,
        "base_cost_ton": 8,
        "base_cost_resource": "scrap",
        "upgrade_requires": "chips",
        "daily_wear": 0.04,
        "description": {"en": "Equipment repair & recycling", "ru": "Ремонт и переработка"},
        "icon": "🔧",
    },
    "vr_club": {
        "name": {"en": "VR Club", "ru": "VR Клуб"},
        "tier": 2,
        "produces": None,  # Entertainment service
        "consumes": ["cu", "traffic", "cooling"],
        "base_production": 0,
        "base_income": 0,
        "base_cost_ton": 18,
        "base_cost_resource": "chips",
        "upgrade_requires": "nft",
        "daily_wear": 0.05,
        "description": {"en": "Virtual reality entertainment", "ru": "VR развлечения"},
        "icon": "🥽",
    },
    
    # ===== TIER III (30% tax) - Financial/Entertainment =====
    "validator": {
        "name": {"en": "Validator Node", "ru": "Валидатор"},
        "tier": 3,
        "produces": None,  # Patron business
        "consumes": ["cu", "cooling", "energy", "traffic"],
        "base_production": 0,
        "base_income": 0,
        "base_cost_ton": 50,
        "base_cost_resource": "algo",
        "upgrade_requires": "chips",
        "daily_wear": 0.07,
        "description": {"en": "Blockchain validator (+production buff)", "ru": "Валидатор блокчейна (+бонус производства)"},
        "icon": "⚡",
        "is_patron": True,
        "patron_type": "validator",
    },
    "gram_bank": {
        "name": {"en": "Gram Bank", "ru": "Грам Банк"},
        "tier": 3,
        "produces": None,
        "consumes": ["cu", "traffic", "algo"],
        "base_production": 0,
        "base_income": 0,
        "base_cost_ton": 60,
        "base_cost_resource": "nft",
        "upgrade_requires": "algo",
        "daily_wear": 0.04,
        "description": {"en": "Banking services (+income buff)", "ru": "Банковские услуги (+бонус дохода)"},
        "icon": "🏦",
        "is_patron": True,
        "patron_type": "gram_bank",
        "instant_withdrawal": True,  # Can provide instant withdrawal
    },
    "dex": {
        "name": {"en": "DEX Exchange", "ru": "DEX Биржа"},
        "tier": 3,
        "produces": None,
        "consumes": ["cu", "traffic", "algo"],
        "base_production": 0,
        "base_income": 0,
        "base_cost_ton": 55,
        "base_cost_resource": "algo",
        "upgrade_requires": "nft",
        "daily_wear": 0.05,
        "description": {"en": "Decentralized exchange (+trade buff)", "ru": "Децентрализованная биржа (+бонус торговли)"},
        "icon": "📊",
        "is_patron": True,
        "patron_type": "dex",
    },
    "casino": {
        "name": {"en": "Crypto Casino", "ru": "Крипто Казино"},
        "tier": 3,
        "produces": None,
        "consumes": ["energy", "traffic", "nft"],
        "base_production": 0,
        "base_income": 0,
        "base_cost_ton": 70,
        "base_cost_resource": "nft",
        "upgrade_requires": "algo",
        "daily_wear": 0.06,
        "description": {"en": "Gambling entertainment (+luck buff)", "ru": "Азартные игры (+бонус удачи)"},
        "icon": "🎰",
        "is_patron": True,
        "patron_type": "casino",
    },
    "arena": {
        "name": {"en": "Battle Arena", "ru": "Боевая Арена"},
        "tier": 3,
        "produces": None,
        "consumes": ["energy", "traffic", "cu"],
        "base_production": 0,
        "base_income": 0,
        "base_cost_ton": 45,
        "base_cost_resource": "chips",
        "upgrade_requires": "nft",
        "daily_wear": 0.05,
        "description": {"en": "PvP competitions (+reputation buff)", "ru": "PvP соревнования (+бонус репутации)"},
        "icon": "⚔️",
        "is_patron": True,
        "patron_type": "arena",
    },
    "incubator": {
        "name": {"en": "Startup Incubator", "ru": "Инкубатор стартапов"},
        "tier": 3,
        "produces": None,
        "consumes": ["cu", "algo", "traffic"],
        "base_production": 0,
        "base_income": 0,
        "base_cost_ton": 40,
        "base_cost_resource": "algo",
        "upgrade_requires": "nft",
        "daily_wear": 0.03,
        "description": {"en": "Startup acceleration (-upgrade cost)", "ru": "Ускоритель стартапов (-стоимость улучшений)"},
        "icon": "🚀",
        "is_patron": True,
        "patron_type": "incubator",
    },
    "bridge": {
        "name": {"en": "Cross-Chain Bridge", "ru": "Кросс-чейн мост"},
        "tier": 3,
        "produces": None,
        "consumes": ["cu", "traffic", "algo"],
        "base_production": 0,
        "base_income": 0,
        "base_cost_ton": 48,
        "base_cost_resource": "algo",
        "upgrade_requires": "chips",
        "daily_wear": 0.04,
        "description": {"en": "Cross-chain transfers (-transfer fees)", "ru": "Кросс-чейн переводы (-комиссия переводов)"},
        "icon": "🌉",
        "is_patron": True,
        "patron_type": "bridge",
    },
}

# Upgrade cost multiplier per level
UPGRADE_MULTIPLIER = 1.8

# Warehouse configurations
WAREHOUSE_CONFIG = {
    "base_capacity_multiplier": 5,  # Base storage = production * 5
    "additional_warehouse_cost_ton": 10,
    "additional_warehouse_base_capacity": 100,
    "max_additional_warehouses": 3,
    "warehouse_upgrade_multiplier": 1.5,
    "rental_tax_rate": 0.15,  # 15% tax on rental income
}

# Patron tax rate
PATRON_TAX_RATE = 0.01  # 1% to patron

# Instant withdrawal fee
INSTANT_WITHDRAWAL_FEE = 0.01  # 1% to bank


def calculate_upgrade_cost(business_type: str, current_level: int) -> dict:
    """Calculate upgrade cost for next level"""
    config = BUSINESSES.get(business_type)
    if not config:
        return None
    
    base_ton = config["base_cost_ton"]
    base_resource = config["base_cost_resource"]
    upgrade_resource = config["upgrade_requires"]
    
    multiplier = UPGRADE_MULTIPLIER ** (current_level)
    
    ton_cost = base_ton * multiplier
    resource_cost = int(10 * multiplier) if upgrade_resource else 0
    
    return {
        "ton": round(ton_cost, 2),
        "resource_type": upgrade_resource,
        "resource_amount": resource_cost,
    }


def calculate_production(business_type: str, level: int, durability: float, patron_bonus: float = 1.0) -> float:
    """Calculate current production rate"""
    config = BUSINESSES.get(business_type)
    if not config:
        return 0
    
    base = config["base_production"]
    # Level multiplier: each level adds 20%
    level_mult = 1 + (level - 1) * 0.2
    # Durability affects production
    durability_mult = durability / 100
    
    return base * level_mult * durability_mult * patron_bonus


def calculate_income(business_type: str, level: int, durability: float, patron_bonus: float = 1.0) -> float:
    """Calculate income per hour"""
    config = BUSINESSES.get(business_type)
    if not config:
        return 0
    
    base = config["base_income"]
    # Level multiplier
    level_mult = 1 + (level - 1) * 0.25
    # Durability affects income
    durability_mult = durability / 100
    
    return base * level_mult * durability_mult * patron_bonus


def calculate_repair_cost(business_type: str, level: int) -> float:
    """Calculate repair cost (10% of daily income)"""
    hourly_income = calculate_income(business_type, level, 100)
    daily_income = hourly_income * 24
    return round(daily_income * 0.1, 4)


def get_daily_wear(business_type: str, level: int) -> float:
    """Get daily wear percentage based on business type and level"""
    config = BUSINESSES.get(business_type)
    if not config:
        return 0.05
    
    base_wear = config["daily_wear"]
    # Higher levels have slightly more wear (more complex equipment)
    level_modifier = 1 + (level - 1) * 0.01
    return min(base_wear * level_modifier, 0.10)  # Cap at 10%


def get_storage_capacity(business_type: str, level: int) -> int:
    """Calculate built-in storage capacity"""
    production = calculate_production(business_type, level, 100)
    return int(production * WAREHOUSE_CONFIG["base_capacity_multiplier"])


def get_patron_bonus(patron_type: str, patron_level: int, bonus_type: str) -> float:
    """Calculate patron bonus multiplier"""
    patron_config = PATRON_BONUSES.get(patron_type)
    if not patron_config or patron_config["type"] != bonus_type:
        return 1.0
    
    min_mult, max_mult = patron_config["multiplier_range"]
    # Linear interpolation based on patron level (1-10)
    progress = (patron_level - 1) / 9
    
    if bonus_type in ["upgrade", "transfer"]:
        # For these, lower is better
        return max_mult + (min_mult - max_mult) * (1 - progress)
    else:
        return min_mult + (max_mult - min_mult) * progress


def check_resource_requirements(business_type: str, level: int, available_resources: dict) -> dict:
    """
    Check if business has enough resources to operate.
    Returns dict with status and missing resources.
    """
    config = BUSINESSES.get(business_type)
    if not config:
        return {"can_operate": False, "missing": [], "reason": "unknown_business"}
    
    consumes = config.get("consumes", [])
    if not consumes:
        # No resource requirements
        return {"can_operate": True, "missing": [], "reason": None}
    
    missing = []
    production = calculate_production(business_type, level, 100)
    
    for resource in consumes:
        # Daily consumption = production rate * 0.1 (10% of production as consumption)
        daily_required = int(production * 0.1) + 1
        available = available_resources.get(resource, 0)
        
        if available < daily_required:
            missing.append({
                "resource": resource,
                "required": daily_required,
                "available": available,
                "deficit": daily_required - available
            })
    
    return {
        "can_operate": len(missing) == 0,
        "missing": missing,
        "reason": "missing_resources" if missing else None
    }


# Level configurations for all 10 levels
LEVEL_CONFIG = {
    1: {"income_mult": 1.0, "production_mult": 1.0, "storage_mult": 1.0, "upgrade_cost_mult": 1.0},
    2: {"income_mult": 1.25, "production_mult": 1.2, "storage_mult": 1.3, "upgrade_cost_mult": 1.8},
    3: {"income_mult": 1.55, "production_mult": 1.45, "storage_mult": 1.7, "upgrade_cost_mult": 3.24},
    4: {"income_mult": 1.9, "production_mult": 1.75, "storage_mult": 2.2, "upgrade_cost_mult": 5.83},
    5: {"income_mult": 2.35, "production_mult": 2.1, "storage_mult": 2.8, "upgrade_cost_mult": 10.5},
    6: {"income_mult": 2.9, "production_mult": 2.5, "storage_mult": 3.5, "upgrade_cost_mult": 18.9},
    7: {"income_mult": 3.6, "production_mult": 3.0, "storage_mult": 4.3, "upgrade_cost_mult": 34.0},
    8: {"income_mult": 4.5, "production_mult": 3.6, "storage_mult": 5.2, "upgrade_cost_mult": 61.2},
    9: {"income_mult": 5.6, "production_mult": 4.3, "storage_mult": 6.2, "upgrade_cost_mult": 110.2},
    10: {"income_mult": 7.0, "production_mult": 5.2, "storage_mult": 7.5, "upgrade_cost_mult": 198.4},
}


def get_business_full_stats(business_type: str, level: int = 1) -> dict:
    """
    Get complete stats for a business at a specific level.
    Returns all production, income, costs, and requirements.
    """
    config = BUSINESSES.get(business_type)
    if not config:
        return None
    
    level_cfg = LEVEL_CONFIG.get(level, LEVEL_CONFIG[1])
    tier = config.get("tier", 1)
    tax_rate = TIER_TAXES.get(tier, 0.15)
    
    # Calculate production
    base_prod = config.get("base_production", 0)
    production = base_prod * level_cfg["production_mult"]
    
    # Calculate income
    base_income = config.get("base_income", 0)
    gross_income = base_income * level_cfg["income_mult"]
    net_income = gross_income * (1 - tax_rate)
    
    # Calculate costs
    base_cost = config.get("base_cost_ton", 5)
    upgrade_cost = base_cost * level_cfg["upgrade_cost_mult"] if level < 10 else None
    
    # Maintenance cost (based on tier and level)
    maintenance = MAINTENANCE_COSTS.get(tier, {}).get(level, 0.05)
    
    # Daily consumption
    consumes = config.get("consumes", [])
    daily_consumption = {}
    for resource in consumes:
        # Consumption scales with production
        daily_consumption[resource] = int(production * 0.1) + level
    
    # Storage capacity
    storage_capacity = get_storage_capacity(business_type, level)
    
    return {
        "business_type": business_type,
        "name": config.get("name", {}),
        "tier": tier,
        "level": level,
        "max_level": 10,
        "icon": config.get("icon", "🏢"),
        "production": {
            "resource": config.get("produces"),
            "amount_per_hour": round(production, 2),
            "amount_per_day": round(production * 24, 2),
        },
        "income": {
            "gross_per_hour": round(gross_income, 6),
            "net_per_hour": round(net_income, 6),
            "gross_per_day": round(gross_income * 24, 4),
            "net_per_day": round(net_income * 24, 4),
            "tax_rate": tax_rate,
            "tax_percent": f"{tax_rate * 100:.0f}%"
        },
        "costs": {
            "build_cost": base_cost,
            "upgrade_cost": round(upgrade_cost, 2) if upgrade_cost else None,
            "maintenance_daily": maintenance,
        },
        "consumption": daily_consumption,
        "storage_capacity": storage_capacity,
        "upgrade_requires": config.get("upgrade_requires"),
        "roi_days": round((base_cost * level_cfg["upgrade_cost_mult"]) / (net_income * 24), 1) if net_income > 0 else 999,
    }


def get_all_businesses_by_level() -> dict:
    """
    Get stats for all 21 businesses at all 10 levels.
    Used for income table and game balance.
    """
    result = {}
    
    for biz_type in BUSINESSES.keys():
        result[biz_type] = {}
        for level in range(1, 11):
            result[biz_type][level] = get_business_full_stats(biz_type, level)
    
    return result


# Maintenance costs by tier and level (daily TON cost)
MAINTENANCE_COSTS = {
    1: {1: 0.05, 2: 0.08, 3: 0.12, 4: 0.18, 5: 0.25, 6: 0.35, 7: 0.48, 8: 0.65, 9: 0.85, 10: 1.10},
    2: {1: 0.50, 2: 0.80, 3: 1.20, 4: 1.80, 5: 2.50, 6: 3.50, 7: 4.80, 8: 6.50, 9: 8.50, 10: 11.00},
    3: {1: 5.00, 2: 8.00, 3: 12.00, 4: 18.00, 5: 25.00, 6: 35.00, 7: 48.00, 8: 65.00, 9: 85.00, 10: 120.00},
}

