from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime, timezone, timedelta
from jose import JWTError, jwt
import math
import asyncio
import json
from tonsdk.utils import Address

# Import TON integration and background tasks
from ton_integration import ton_client, init_ton_client, close_ton_client, validate_ton_address
from background_tasks import (
    init_scheduler, start_scheduler, shutdown_scheduler, 
    trigger_auto_collection_now
)
from payment_monitor import init_payment_monitor, stop_payment_monitor

# Import new business system V2.0
from business_config import (
    BUSINESSES, TIER_TAXES, PATRON_BONUSES, RESOURCE_WEIGHTS, RESOURCE_TYPES,
    WAREHOUSE_CONFIG, PATRON_TAX_RATE, INSTANT_WITHDRAWAL_FEE, TURNOVER_TAX_RATE,
    MAINTENANCE_COSTS, BUSINESS_LEVELS, MIDNIGHT_DECAY_RATE, MIN_PRICE_TON,
    NPC_PRICE_FLOOR, NPC_PRICE_CEILING, MONOPOLY_THRESHOLD,
    ESTIMATED_DAILY_INCOME, PATRONAGE_EFFECTS, UPGRADE_COST_MULTIPLIER,
    calculate_upgrade_cost, get_production, get_consumption, get_consumption_breakdown,
    calculate_effective_production, calculate_effective_income,
    get_daily_wear, get_storage_capacity, get_expansion_slot_capacity,
    get_patron_bonus, check_resource_requirements, calculate_repair_cost,
    get_business_full_stats, get_all_businesses_summary,
    get_estimated_daily_income, get_patron_effect,
)
from game_systems import (
    PatronageSystem, BusinessEconomics, WarehouseSystem,
    TaxSystem, NPCMarketSystem, InflationSystem, BankruptcySystem,
    EventsSystem, EconomicTickEngine, IncomeCollector, BankingSystem,
)
from ton_island import generate_ton_island_map, get_cell_at, get_neighbors, ZONES

# Import business financial model
from business_model import (
    get_production_at_level, get_requirements_at_level, get_upgrade_cost,
    get_business_tier, get_tax_rate_for_business, get_all_levels_info,
    BUSINESS_TIERS, BUSINESS_NAMES_RU, TIER_NAMES,
    BASE_PRODUCTION, BASE_REQUIREMENTS, LEVEL_MULTIPLIERS, UPGRADE_COSTS
)

# Import chat handler
from chat_handler import chat_router, set_db as set_chat_db, chat_websocket_handler

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'ton-city-builder-secret-key-2025')
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'admin-secret-key-2025')
ADMIN_WALLET = os.environ.get('ADMIN_WALLET_ADDRESS') or os.environ.get('ADMIN_WALLET') or None
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

# Create the main app
app = FastAPI(title="TON City Builder API")
api_router = APIRouter(prefix="/api")
admin_router = APIRouter(prefix="/api/admin")
public_router = APIRouter(prefix="/api/public")  # Public endpoints without auth
security = HTTPBearer(auto_error=False)
oauth2_scheme = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Online users tracking
online_users = set()
last_activity = {}

# TON address helper functions
def to_raw(address_str):
    """Convert TON address to raw format"""
    try:
        return Address(address_str).to_string(is_user_friendly=False)
    except Exception:
        return address_str

def to_user_friendly(raw_address):
    """Convert raw TON address to user-friendly format"""
    try:
        return Address(raw_address).to_string(is_user_friendly=True, is_bounceable=True)
    except Exception:
        return raw_address


# ==================== GAME CONSTANTS ====================

RESALE_COMMISSION = 0.15  # 15% tax on resale to prevent speculation
DEMOLISH_COST = 0.05  # 5% of business cost to demolish

# ==================== OWNERSHIP HELPER ====================
async def get_user_identifiers(current_user) -> dict:
    """Get all possible user identifiers for ownership checks"""
    user = None
    if current_user.wallet_address:
        user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if not user and current_user.email:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    if not user:
        user = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    if not user:
        return {"user": None, "ids": set()}
    
    user_id = user.get("id", str(user.get("_id", "")))
    ids = {user_id, current_user.wallet_address, current_user.id}
    if user.get("wallet_address"):
        ids.add(user.get("wallet_address"))
    if user.get("email"):
        ids.add(user.get("email"))
    ids.discard(None)
    ids.discard("")
    return {"user": user, "ids": ids}

def is_owner(business: dict, user_ids: set) -> bool:
    """Check if business belongs to any of user's identifiers"""
    owner = business.get("owner", "")
    owner_wallet = business.get("owner_wallet", "")
    return owner in user_ids or owner_wallet in user_ids

def get_user_filter(user: dict) -> dict:
    """Get MongoDB filter to find user by best available identifier"""
    if user.get("email"):
        return {"email": user["email"]}
    if user.get("wallet_address"):
        return {"wallet_address": user["wallet_address"]}
    return {"id": user.get("id")}

def get_businesses_query(user_ids: set) -> dict:
    """Get MongoDB query to find businesses by any user identifier"""
    or_conditions = [{"owner": uid} for uid in user_ids]
    or_conditions.extend([{"owner_wallet": uid} for uid in user_ids])
    return {"$or": or_conditions}
TRADE_COMMISSION = 0.0  # No trade commission - income tax applies when user receives money
RENTAL_COMMISSION = 0.10
WITHDRAWAL_COMMISSION = 0.03
MIN_WITHDRAWAL = 1.0
BASE_TAX_RATE = 0.10
PROGRESSIVE_TAX = {
    0.05: 0.12,
    0.10: 0.15,
    0.15: 0.18,
    0.20: 0.22,
    0.25: 0.25,
}

# Level system multipliers
LEVEL_CONFIG = {
    1: {"xp_required": 0, "income_mult": 1.0, "speed_mult": 1.0, "bonus": None, "upgrade_cost": 0},
    2: {"xp_required": 100, "income_mult": 1.2, "speed_mult": 1.1, "bonus": "upgrades", "upgrade_cost": 5},
    3: {"xp_required": 300, "income_mult": 1.5, "speed_mult": 1.2, "bonus": "discount_5", "upgrade_cost": 10},
    4: {"xp_required": 600, "income_mult": 1.8, "speed_mult": 1.3, "bonus": "storage", "upgrade_cost": 20},
    5: {"xp_required": 1000, "income_mult": 2.2, "speed_mult": 1.5, "bonus": "automation_1", "upgrade_cost": 35},
    6: {"xp_required": 1500, "income_mult": 2.7, "speed_mult": 1.7, "bonus": "discount_10", "upgrade_cost": 50},
    7: {"xp_required": 2200, "income_mult": 3.3, "speed_mult": 2.0, "bonus": "automation_2", "upgrade_cost": 75},
    8: {"xp_required": 3000, "income_mult": 4.0, "speed_mult": 2.3, "bonus": "vip", "upgrade_cost": 100},
    9: {"xp_required": 4000, "income_mult": 5.0, "speed_mult": 2.7, "bonus": "franchise", "upgrade_cost": 150},
    10: {"xp_required": 5500, "income_mult": 6.5, "speed_mult": 3.0, "bonus": "corporation", "upgrade_cost": 200},
}

# Player levels
PLAYER_LEVELS = {
    "novice": {"min_turnover": 0, "max_plots": 3, "max_market_share": 0.05},
    "entrepreneur": {"min_turnover": 100, "max_plots": 7, "max_market_share": 0.10},
    "businessman": {"min_turnover": 500, "max_plots": 15, "max_market_share": 0.15},
    "magnate": {"min_turnover": 2000, "max_plots": 30, "max_market_share": 0.20},
    "oligarch": {"min_turnover": 10000, "max_plots": 50, "max_market_share": 0.25},
    1: {"min_turnover": 0, "max_plots": 3, "max_market_share": 0.05},
    2: {"min_turnover": 50, "max_plots": 5, "max_market_share": 0.07},
    3: {"min_turnover": 100, "max_plots": 7, "max_market_share": 0.10},
    4: {"min_turnover": 250, "max_plots": 10, "max_market_share": 0.12},
    5: {"min_turnover": 500, "max_plots": 15, "max_market_share": 0.15},
}

# Zone configuration
ZONES = {
    "center": {"radius_max": 10, "plot_limit": 3, "price_mult": 1.0},
    "business": {"radius_max": 25, "plot_limit": 10, "price_mult": 0.7},
    "residential": {"radius_max": 40, "plot_limit": 15, "price_mult": 0.45},
    "industrial": {"radius_max": 50, "plot_limit": 20, "price_mult": 0.25},
    "outskirts": {"radius_max": 100, "plot_limit": 30, "price_mult": 0.12},
}

# Business types with full configuration
BUSINESS_TYPES = {
    "farm": {
        "name": {"en": "Farm", "ru": "Ферма", "zh": "农场"},
        "icon": "🌾",
        "sector": "primary",
        "cost": 5,
        "build_time_hours": 2,
        "materials_required": 50,
        "energy_consumption": 10,
        "produces": "crops",
        "production_rate": 100,
        "requires": None,
        "base_income": 2.4,
        "operating_cost": 0.3,
        "allowed_zones": ["residential", "industrial", "outskirts"],
        "max_per_player": 10,
        "min_builders": 1,
    },
    "power_plant": {
        "name": {"en": "Power Plant", "ru": "Электростанция", "zh": "发电厂"},
        "icon": "⚡",
        "sector": "primary",
        "cost": 20,
        "build_time_hours": 8,
        "materials_required": 300,
        "energy_consumption": 0,
        "produces": "energy",
        "production_rate": 500,
        "requires": None,
        "base_income": 2.4,
        "operating_cost": 0.8,
        "allowed_zones": ["industrial", "outskirts"],
        "max_per_player": 3,
        "min_builders": 2,
    },
    "quarry": {
        "name": {"en": "Quarry", "ru": "Карьер", "zh": "采石场"},
        "icon": "⛏️",
        "sector": "primary",
        "cost": 25,
        "build_time_hours": 10,
        "materials_required": 200,
        "energy_consumption": 80,
        "produces": "materials",
        "production_rate": 50,
        "requires": None,
        "base_income": 6.0,
        "operating_cost": 1.5,
        "allowed_zones": ["industrial", "outskirts"],
        "max_per_player": 5,
        "min_builders": 2,
    },
    "factory": {
        "name": {"en": "Factory", "ru": "Завод", "zh": "工厂"},
        "icon": "🏭",
        "sector": "secondary",
        "cost": 15,
        "build_time_hours": 6,
        "materials_required": 150,
        "energy_consumption": 50,
        "produces": "goods",
        "production_rate": 30,
        "requires": "crops",
        "consumption_rate": 50,
        "base_income": 2.88,
        "operating_cost": 1.44,
        "allowed_zones": ["business", "industrial"],
        "max_per_player": 8,
        "min_builders": 2,
    },
    "shop": {
        "name": {"en": "Shop", "ru": "Магазин", "zh": "商店"},
        "icon": "🏪",
        "sector": "tertiary",
        "cost": 10,
        "build_time_hours": 4,
        "materials_required": 100,
        "energy_consumption": 20,
        "produces": "retail",
        "production_rate": 0,
        "requires": "goods",
        "consumption_rate": 30,
        "base_income": 4.8,
        "operating_cost": 0.5,
        "allowed_zones": ["center", "business", "residential"],
        "max_per_player": 15,
        "min_builders": 1,
        "customer_flow": {"center": 100, "business": 60, "residential": 40},
    },
    "restaurant": {
        "name": {"en": "Restaurant", "ru": "Ресторан", "zh": "餐厅"},
        "icon": "🍽️",
        "sector": "tertiary",
        "cost": 12,
        "build_time_hours": 5,
        "materials_required": 120,
        "energy_consumption": 30,
        "produces": "food_service",
        "production_rate": 30,
        "requires": "crops",
        "consumption_rate": 30,
        "base_income": 5.4,
        "operating_cost": 0.86,
        "allowed_zones": ["center", "business", "residential"],
        "max_per_player": 10,
        "min_builders": 1,
    },
    "bank": {
        "name": {"en": "Bank", "ru": "Банк", "zh": "银行"},
        "icon": "🏦",
        "sector": "quaternary",
        "cost": 50,
        "build_time_hours": 24,
        "materials_required": 500,
        "energy_consumption": 40,
        "produces": "finance",
        "production_rate": 0,
        "requires": None,
        "base_income": 4.5,
        "operating_cost": 0.6,
        "allowed_zones": ["center", "business"],
        "max_per_player": 1,
        "min_builders": 3,
    },
}

# Resource prices (base) - V2.0: All prices >= MIN_PRICE_TON (0.01)
RESOURCE_PRICES = {
    "crops": 0.01,
    "energy": 0.01,
    "materials": 0.01,
    "fuel": 0.01,
    "ore": 0.01,
    "goods": 0.01,
    "refined_fuel": 0.015,
    "steel": 0.012,
    "textiles": 0.01,
    # New V2.0 resources
    "cu": 0.02,
    "quartz": 0.015,
    "traffic": 0.012,
    "cooling": 0.02,
    "biomass": 0.018,
    "scrap": 0.01,
    "chips": 0.10,
    "nft": 0.15,
    "neurocode": 0.20,
    "logistics": 0.05,
    "repair_kits": 0.08,
    "vr_experience": 0.12,
    "shares": 0.50,
}

# ==================== HELPER FUNCTIONS ====================

def calculate_plot_price(x: int, y: int) -> tuple:
    """Calculate plot price and zone based on distance from center"""
    center_x, center_y = 50, 50
    distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    zone = "outskirts"
    for zone_name, config in ZONES.items():
        if distance <= config["radius_max"]:
            zone = zone_name
            break
    
    max_distance = math.sqrt(50**2 + 50**2)
    price = 10 + 90 * (1 - distance / max_distance)
    return round(price, 2), zone

def get_tax_rate(market_share: float) -> float:
    """Get progressive tax rate based on market share"""
    for threshold, rate in sorted(PROGRESSIVE_TAX.items(), reverse=True):
        if market_share >= threshold:
            return rate
    return BASE_TAX_RATE

def calculate_business_income(business_type: str, level: int, zone: str, connections: int) -> dict:
    """Calculate business income with all factors"""
    bt = BUSINESS_TYPES.get(business_type)
    if not bt:
        return {"gross": 0, "tax": 0, "net": 0}
    
    base = bt["base_income"]
    zone_mult = ZONES.get(zone, {}).get("price_mult", 0.5)
    level_mult = LEVEL_CONFIG.get(level, LEVEL_CONFIG[1])["income_mult"]
    conn_bonus = 1 + (connections * 0.05)
    
    gross = base * zone_mult * level_mult * conn_bonus
    tax = gross * BASE_TAX_RATE
    operating = bt.get("operating_cost", 0)
    net = gross - tax - operating
    
    return {
        "gross": round(gross, 4),
        "tax": round(tax, 4),
        "operating_cost": round(operating, 4),
        "net": round(max(0, net), 4)
    }

# Translation helper
def t(key: str, lang: str = "en") -> str:
    """Simple translation helper"""
    translations = {
        "max_plots_reached": {"en": "Maximum plots reached for your level", "ru": "Достигнуто максимальное количество участков для вашего уровня"},
        "plot_not_available": {"en": "Plot not available", "ru": "Участок недоступен"},
        "invalid_zone": {"en": "Business not allowed in this zone", "ru": "Бизнес не разрешён в этой зоне"},
        "plot_purchased": {"en": "Plot purchased successfully", "ru": "Участок успешно приобретён"},
        "business_built": {"en": "Business built successfully", "ru": "Бизнес успешно построен"},
    }
    return translations.get(key, {}).get(lang, key)

# ==================== MODELS ====================

class WithdrawRequest(BaseModel):
    amount: float
    totp_code: Optional[str] = None  # 2FA code required

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: Optional[str] = None
    email: Optional[str] = None
    wallet_address: Optional[str] = None
    raw_address: Optional[str] = None
    display_name: Optional[str] = None
    language: str = "en"
    level: Union[str, int] = "novice"  # Поддержка и str и int
    xp: int = 0
    balance_ton: float = 0.0
    total_turnover: float = 0.0
    total_income: float = 0.0
    plots_owned: List[str] = []
    businesses_owned: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_admin: bool = False

class Plot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    x: int
    y: int
    zone: str = "outskirts"
    price: float = 10.0
    owner: Optional[str] = None
    business_id: Optional[str] = None
    is_available: bool = True
    is_rented: bool = False
    rent_price: Optional[float] = None
    renter: Optional[str] = None
    purchased_at: Optional[datetime] = None

class Business(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plot_id: str
    owner: str
    business_type: str
    level: int = 1
    xp: int = 0
    income_rate: float = 0.0
    production_rate: float = 0.0
    storage: Dict[str, float] = {}
    connected_businesses: List[str] = []
    is_active: bool = True
    last_collection: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    building_progress: float = 100.0  # 0-100%
    builders: List[str] = []

class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tx_type: str
    from_address: str
    to_address: Optional[str] = None
    amount_ton: float
    commission: float = 0.0
    tax: float = 0.0
    plot_id: Optional[str] = None
    business_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_amount: Optional[float] = None
    status: str = "pending"
    blockchain_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class Contract(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    seller_id: str
    buyer_id: str
    seller_business_id: str
    buyer_business_id: str
    resource_type: str
    amount_per_hour: float
    price_per_unit: float
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

class BuildOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plot_id: str
    owner: str
    business_type: str
    status: str = "pending"  # pending, in_progress, completed
    materials_paid: bool = False
    builders: List[str] = []
    builder_payments: Dict[str, float] = {}
    progress: float = 0.0
    estimated_completion: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request models
class PurchasePlotRequest(BaseModel):
    plot_x: int
    plot_y: int

class ResalePlotRequest(BaseModel):
    plot_id: str
    resale_price: float

class BuildBusinessRequest(BaseModel):
    plot_id: str
    business_type: str

class CreateContractRequest(BaseModel):
    seller_business_id: str
    buyer_business_id: str
    resource_type: str
    amount_per_hour: float
    price_per_unit: float

class TradeResourceRequest(BaseModel):
    seller_business_id: str
    buyer_id: str
    resource_type: str
    amount: float
    price_per_unit: float

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# Request models
class WalletVerifyRequest(BaseModel):
    address: str
    proof: Optional[Dict[str, Any]] = None
    language: str = "en"
    username: Optional[str] = None
    email: Optional[str] = None     
    password: Optional[str] = None 

class ConfirmTransactionRequest(BaseModel):
    transaction_id: str
    blockchain_hash: Optional[str] = None

class RentPlotRequest(BaseModel):
    plot_id: str
    rent_price: float

class AcceptRentRequest(BaseModel):
    plot_id: str

# ========================== AUTH ===========================

class EmailRegister(BaseModel):
    email: str
    password: str
    username: str

class WalletAuth(BaseModel):
    address: str
    public_key: Optional[str] = None
    username: Optional[str] = None

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        identifier: str = payload.get("sub")
        if not identifier:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Ищем пользователя по разным полям (wallet_address, email, username)
        user_doc = await db.users.find_one({
            "$or": [
                {"wallet_address": identifier},
                {"email": identifier},
                {"username": identifier}
            ]
        })
        
        if not user_doc:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Normalize is_admin field to boolean
        if "is_admin" in user_doc:
            if isinstance(user_doc["is_admin"], str):
                user_doc["is_admin"] = user_doc["is_admin"].lower() in ("true", "1", "yes")
            elif not isinstance(user_doc["is_admin"], bool):
                user_doc["is_admin"] = False
        else:
            user_doc["is_admin"] = False
        
        # Auto-grant admin if wallet matches ADMIN_WALLET_ADDRESS from env
        wallet_addr = user_doc.get("wallet_address", "") or user_doc.get("wallet_address_raw", "")
        if ADMIN_WALLET and wallet_addr and (wallet_addr == ADMIN_WALLET or wallet_addr.lower() == ADMIN_WALLET.lower()):
            user_doc["is_admin"] = True
        
        return User(**user_doc)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
async def get_current_admin(current_user: User = Depends(get_current_user)):
    # Проверка: либо флаг в БД, либо сверка с кошельком админа из .env
    if not current_user.is_admin and current_user.wallet_address != ADMIN_WALLET:
        raise HTTPException(status_code=403, detail="Доступ запрещен: вы не администратор")
    return current_user

# Alias for compatibility
get_admin_user = get_current_admin

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/verify-wallet")
async def verify_wallet(request: WalletVerifyRequest):
    """Verify wallet connection with DEBUG logging"""
    try:
        # --- ЛОГИРОВАНИЕ ВХОДЯЩИХ ДАННЫХ ---
        print("\n" + "="*50)
        print("🚀 ВХОДЯЩИЙ ЗАПРОС НА АВТОРИЗАЦИЮ")
        print(f"📍 Address: {request.address}")
        print(f"👤 Username: {request.username}")
        print(f"📧 Email: {request.email}")
        print(f"🔑 Password: {'***' if request.password else None}")
        print("="*50 + "\n")

        raw_input = (request.address or "").strip()
        if not raw_input:
            raise HTTPException(status_code=400, detail="Wallet address required")
        
        # Нормализация (используем твои функции из auth_handler или tonsdk)
        wallet_uf = to_user_friendly(raw_input) or (raw_input if raw_input.startswith("0:") else None)
        raw_addr = to_raw(raw_input) or (to_raw(wallet_uf) if wallet_uf else None)
        
        if not wallet_uf or not raw_addr:
            print(f"❌ Ошибка нормализации адреса: {raw_input}")
            raise HTTPException(status_code=400, detail="Invalid TON address format")
        
        wallet_address = wallet_uf
        
        # Поиск пользователя
        user_doc = await db.users.find_one({
            "$or": [{"wallet_address": wallet_address}, {"raw_address": raw_addr}]
        })
        
        if not user_doc:
            print("ℹ️ Пользователь не найден в БД. Попытка регистрации...")
            
            if not request.username:
                print("⚠️ Регистрация прервана: не указан username")
                return {
                    "status": "need_username",
                    "message": "Username required for registration",
                    "wallet_address": wallet_address
                }
            
            # Проверка уникальности username
            existing_username = await db.users.find_one({"username": request.username})
            if existing_username:
                print(f"❌ Ошибка: Username {request.username} уже занят")
                raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
            
            # Проверка уникальности Email (если он прислан)
            if request.email:
                existing_email = await db.users.find_one({"email": request.email})
                if existing_email:
                    print(f"❌ Ошибка: Email {request.email} уже занят")
                    raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

            # Импортируем функцию генерации аватара
            from auth_handler import generate_avatar_from_initials, pwd_context
            
            # Генерируем аватар из username
            avatar = generate_avatar_from_initials(request.username)
            
            # Хешируем пароль если он есть
            hashed_password = None
            if request.password:
                hashed_password = pwd_context.hash(request.password)

            # Формируем объект для записи
            import uuid
            new_user = {
                "id": str(uuid.uuid4()),
                "wallet_address": wallet_address,
                "raw_address": raw_addr,
                "username": request.username,
                "display_name": request.username,
                "email": request.email,
                "hashed_password": hashed_password,
                "avatar": avatar,
                "language": request.language or "en",
                "is_admin": False,
                "balance_ton": 0.0,
                "level": 1,
                "xp": 0,
                "total_turnover": 0,
                "total_income": 0.0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": datetime.now(timezone.utc).isoformat(),
                "plots_owned": [],
                "businesses_owned": []
            }

            # --- ЛОГ ПЕРЕД ЗАПИСЬЮ В БД ---
            print("📝 ПОПЫТКА ЗАПИСИ В MONGODB:")
            print(json.dumps({**new_user, "hashed_password": "***" if hashed_password else None}, indent=2, ensure_ascii=False))
            
            try:
                result = await db.users.insert_one(new_user)
                print(f"✅ УСПЕШНО ЗАПИСАНО. ID: {result.inserted_id}")
                user_doc = new_user
            except Exception as db_err:
                print(f"❌ КРИТИЧЕСКАЯ ОШИБКА MONGODB: {db_err}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")
        else:
            print(f"✅ Пользователь найден: {user_doc.get('username')}. Обновляем вход.")
            update_data = {
                "last_login": datetime.now(timezone.utc).isoformat(), 
                "language": request.language
            }
            # Обновляем email/pass только если они присланы и их нет в базе
            if request.email and not user_doc.get("email"):
                update_data["email"] = request.email
            if request.password and not user_doc.get("password"):
                update_data["password"] = request.password

            await db.users.update_one({"_id": user_doc["_id"]}, {"$set": update_data})
            user_doc.update(update_data)
        
        # Создаем токен
        from auth_handler import create_token
        token = create_token(data={"sub": wallet_address})
        print(f"🎫 JWT токен сгенерирован для: {wallet_address}")
        
        return {
            "status": "ok",
            "token": token,
            "user": {
                "id": user_doc.get("id", str(user_doc.get("_id"))),
                "username": user_doc.get("username"),
                "display_name": user_doc.get("display_name") or user_doc.get("username"),
                "wallet_address": wallet_address,
                "email": user_doc.get("email"),
                "avatar": user_doc.get("avatar"),
                "level": user_doc.get("level", 1),
                "is_admin": user_doc.get("is_admin", False)
            }
        }

    except Exception as e:
        print(f"💥 ОШИБКА В РОУТЕ verify_wallet: {str(e)}")
        logger.error(f"Full traceback: ", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    # Ищем пользователя по разным полям
    user_doc = None
    if current_user.wallet_address:
        user_doc = await db.users.find_one({"wallet_address": current_user.wallet_address})
    elif current_user.email:
        user_doc = await db.users.find_one({"email": current_user.email})
    elif current_user.username:
        user_doc = await db.users.find_one({"username": current_user.username})
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    raw = user_doc.get("raw_address") or to_raw(user_doc.get("wallet_address") or "")
    display = user_doc.get("wallet_address")
    
    # Определяем тип аутентификации
    has_password = bool(user_doc.get("hashed_password"))
    has_google = bool(user_doc.get("google_id"))
    has_wallet = bool(user_doc.get("wallet_address"))
    
    if has_google:
        auth_type = "google"
    elif has_wallet and not has_password:
        auth_type = "wallet"
    else:
        auth_type = "email"

    # Check 2FA status
    has_2fa = bool(user_doc.get("is_2fa_enabled", False))
    has_two_factor_secret = bool(user_doc.get("two_factor_secret"))
    has_passkeys = bool(user_doc.get("passkeys") and len(user_doc.get("passkeys", [])) > 0)

    return {
        "id": user_doc.get("id", str(user_doc.get("_id"))),
        "username": user_doc.get("username"),
        "display_name": user_doc.get("display_name") or user_doc.get("username"),
        "email": user_doc.get("email"),
        "avatar": user_doc.get("avatar"),
        "wallet_address": user_doc.get("wallet_address"),
        "wallet_address_raw": raw,
        "wallet_address_display": display,
        "language": user_doc.get("language", "en"),
        "level": user_doc.get("level", 1),
        "xp": user_doc.get("xp", 0),
        "balance_ton": user_doc.get("balance_ton", 0.0),
        "total_turnover": user_doc.get("total_turnover", 0.0),
        "total_income": user_doc.get("total_income", 0.0),
        "plots_owned": user_doc.get("plots_owned", []),
        "businesses_owned": user_doc.get("businesses_owned", []),
        "is_admin": user_doc.get("is_admin", False),
        "is_bank": user_doc.get("is_bank", False),
        "is_2fa_enabled": has_2fa or has_two_factor_secret,
        "has_passkeys": has_passkeys,
        "max_plots": 999 if user_doc.get("is_admin", False) or user_doc.get("is_bank", False) or user_doc.get("role") in ["ADMIN", "BANK"] else 3,
        "auth_type": auth_type
    }

@api_router.get("/users/me/plots")
async def get_my_plots(current_user: User = Depends(get_current_user)):
    """Получить все участки пользователя"""
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        return {"plots": [], "total": 0}
    
    user_ids = ui["ids"]
    plots = []
    
    # Ищем участки в старой коллекции plots
    old_plots = await db.plots.find({
        "$or": [{"owner": uid} for uid in user_ids]
    }, {"_id": 0}).to_list(100)
    
    for plot in old_plots:
        city = await db.cities.find_one({"id": plot.get("city_id")}, {"_id": 0, "name": 1})
        plot["city_name"] = city.get("name", "Город") if city else "Город"
        plots.append(plot)
    
    # Ищем участки на TON Island
    island = await db.islands.find_one({"id": "ton_island"})
    if island and 'cells' in island:
        for cell in island['cells']:
            cell_owner = cell.get('owner')
            if cell_owner and cell_owner in user_ids:
                zone_name = cell.get('zone', 'outskirts')
                zone_names = {
                    'center': 'Центр',
                    'business': 'Бизнес-район',
                    'residential': 'Жилой район',
                    'industrial': 'Промзона',
                    'outskirts': 'Окраина'
                }
                plots.append({
                    "id": f"island_{cell.get('x')}_{cell.get('y')}",
                    "x": cell.get('x'),
                    "y": cell.get('y'),
                    "price": cell.get('price', 0),
                    "city_name": zone_names.get(zone_name, 'TON Island'),
                    "zone": zone_name,
                    "business": cell.get('business'),
                    "is_island": True
                })
    
    return {"plots": plots, "total": len(plots)}

@api_router.get("/users/me/businesses")
async def get_my_businesses(current_user: User = Depends(get_current_user)):
    """Получить все бизнесы пользователя"""
    # Search by both user.id and wallet_address for compatibility
    query = {"$or": [
        {"owner": current_user.id},
        {"owner": current_user.wallet_address}
    ]} if current_user.wallet_address else {"owner": current_user.id}
    
    businesses = await db.businesses.find(query, {"_id": 0}).to_list(100)
    
    # Добавляем информацию о типе бизнеса
    for biz in businesses:
        bt = BUSINESS_TYPES.get(biz.get("business_type"), {})
        biz["produces"] = bt.get("produces")
        biz["consumes"] = bt.get("consumes", [])
    
    return {"businesses": businesses, "total": len(businesses)}

# ==================== LEADERBOARD ====================

@api_router.get("/leaderboard")
async def get_leaderboard(sort_by: str = "balance", limit: int = 50):
    """Получить рейтинг игроков"""
    sort_field_map = {
        "balance": "balance_ton",
        "income": "total_income",
        "businesses": "businesses_count",
        "plots": "plots_count"
    }
    
    sort_field = sort_field_map.get(sort_by, "balance_ton")
    
    # Получаем всех пользователей
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    
    # Добавляем подсчёт бизнесов и участков
    for user in users:
        wallet = user.get("wallet_address")
        user_id = user.get("id")
        
        # Считаем бизнесы - по user_id (основной) или owner_wallet (резервный)
        biz_count = 0
        if user_id:
            biz_count = await db.businesses.count_documents({
                "$or": [
                    {"owner": user_id},
                    {"owner_wallet": wallet}
                ]
            })
        user["businesses_count"] = biz_count
        
        # Считаем участки
        plots_count = await db.plots.count_documents({
            "$or": [
                {"owner": user_id},
                {"owner": wallet}
            ]
        }) if (user_id or wallet) else 0
        user["plots_count"] = plots_count
    
    # Сортируем
    users.sort(key=lambda x: x.get(sort_field, 0), reverse=True)
    
    return {"players": users[:limit], "total": len(users)}

# ==================== TON ISLAND ROUTES ====================

@api_router.get("/config")
async def get_app_config():
    """Get application configuration"""
    return {
        "support_telegram": os.environ.get("SUPPORT_TELEGRAM", "https://t.me/support"),
        "businesses": {k: {
            "name": v["name"],
            "tier": v["tier"],
            "icon": v["icon"],
            "produces": v["produces"],
            "consumes": v.get("consumes", []),
            "is_patron": v.get("is_patron", False),
            "patron_type": v.get("patron_type"),
            "description": v["description"],
        } for k, v in BUSINESSES.items()},
        "tier_taxes": TIER_TAXES,
        "resource_weights": RESOURCE_WEIGHTS,
        "zones": ZONES,
        "patron_bonuses": PATRON_BONUSES,
    }

@api_router.get("/island")
async def get_ton_island():
    """Get TON Island map data"""
    # Check if island exists in DB
    island = await db.islands.find_one({"id": "ton_island"}, {"_id": 0})
    
    if not island:
        # Generate and store
        island = generate_ton_island_map()
        await db.islands.insert_one(island.copy())
    
    # Merge ownership data from plots collection
    plots = await db.plots.find({"island_id": "ton_island"}, {"_id": 0}).to_list(1000)
    plots_map = {(p["x"], p["y"]): p for p in plots}
    
    # Merge businesses data
    businesses = await db.businesses.find({"island_id": "ton_island"}, {"_id": 0}).to_list(1000)
    businesses_map = {(b["x"], b["y"]): b for b in businesses}
    
    cells = island.get("cells", [])
    
    # Collect unique owner IDs to batch load avatars
    owner_ids = set()
    for cell in cells:
        x, y = cell["x"], cell["y"]
        plot = plots_map.get((x, y))
        if plot and plot.get("owner"):
            owner_ids.add(plot.get("owner"))
    
    # Load user avatars
    users_with_avatars = {}
    if owner_ids:
        users = await db.users.find(
            {"$or": [{"id": {"$in": list(owner_ids)}}, {"wallet_address": {"$in": list(owner_ids)}}]},
            {"_id": 0, "id": 1, "wallet_address": 1, "avatar": 1, "username": 1}
        ).to_list(100)
        for u in users:
            users_with_avatars[u.get("id")] = u
            if u.get("wallet_address"):
                users_with_avatars[u.get("wallet_address")] = u
    
    for cell in cells:
        x, y = cell["x"], cell["y"]
        plot = plots_map.get((x, y))
        if plot:
            cell["owner"] = plot.get("owner")
            cell["owner_username"] = plot.get("owner_username")
            # Get avatar from user if not in plot
            owner_user = users_with_avatars.get(plot.get("owner"))
            cell["owner_avatar"] = plot.get("owner_avatar") or (owner_user.get("avatar") if owner_user else None)
        
        business = businesses_map.get((x, y))
        if business:
            cell["business"] = {
                "id": business.get("id"),
                "type": business.get("business_type"),
                "level": business.get("level", 1),
                "tier": BUSINESSES.get(business.get("business_type"), {}).get("tier", 1),
                "icon": BUSINESSES.get(business.get("business_type"), {}).get("icon", "🏢")
            }
    
    # Count statistics
    owned = sum(1 for c in cells if c.get("owner"))
    with_business = sum(1 for c in cells if c.get("business"))
    
    island["stats"] = {
        "total_cells": len(cells),
        "owned_cells": owned,
        "available_cells": len(cells) - owned,
        "businesses": with_business,
    }
    
    return island

@api_router.post("/island/buy/{x}/{y}")
async def buy_island_plot(x: int, y: int, current_user: User = Depends(get_current_user)):
    """Buy a plot on TON Island"""
    # Get island
    island = await db.islands.find_one({"id": "ton_island"}, {"_id": 0})
    if not island:
        island = generate_ton_island_map()
        await db.islands.insert_one(island.copy())
    
    # Find cell
    cell = None
    for c in island["cells"]:
        if c["x"] == x and c["y"] == y:
            cell = c
            break
    
    if not cell:
        raise HTTPException(status_code=404, detail="Участок не найден")
    
    # Check if already owned
    existing = await db.plots.find_one({"island_id": "ton_island", "x": x, "y": y})
    if existing:
        raise HTTPException(status_code=400, detail="Участок уже куплен")
    
    # Get user - search by wallet_address OR email
    user = None
    if current_user.wallet_address:
        user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if not user and current_user.email:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Check plot limit - 3 plots max for regular users, unlimited for admins and banks
    is_admin = user.get("is_admin", False) or user.get("role") == "ADMIN"
    is_bank = user.get("is_bank", False) or user.get("role") == "BANK"
    
    if not is_admin and not is_bank:
        # Count current plots owned by this user
        user_id = user.get("id", str(user.get("_id")))
        current_plots = await db.plots.count_documents({
            "$or": [
                {"owner": user_id},
                {"owner": current_user.wallet_address},
                {"owner": current_user.email}
            ]
        })
        max_plots = 3  # Fixed limit of 3 plots for all regular users
        if current_plots >= max_plots:
            raise HTTPException(status_code=400, detail="max_plots_reached")
    
    price = cell["price"]
    
    # Check balance
    if user.get("balance_ton", 0) < price:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    
    user_id = user.get("id", str(user.get("_id")))
    
    # Create plot
    plot = {
        "id": str(uuid.uuid4()),
        "island_id": "ton_island",
        "x": x,
        "y": y,
        "zone": cell["zone"],
        "price": price,
        "owner": user_id,
        "owner_username": user.get("username"),
        "owner_avatar": user.get("avatar"),
        "business": None,
        "warehouses": [],  # Additional warehouses
        "purchased_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.plots.insert_one(plot.copy())
    
    # Deduct balance - search by email or wallet_address
    user_filter = {"email": user.get("email")} if user.get("email") else {"wallet_address": current_user.wallet_address}
    await db.users.update_one(
        user_filter,
        {"$inc": {"balance_ton": -price}}
    )
    
    # Tax to treasury
    tax = price * 0.05  # 5% purchase tax
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"land_tax": tax, "total_tax": tax}},
        upsert=True
    )
    
    # Record transaction for history
    tx = {
        "id": str(uuid.uuid4()),
        "type": "land_purchase",
        "user_id": user_id,
        "amount_ton": -price,
        "tax": tax,
        "plot_id": plot["id"],
        "plot_coords": f"[{x}, {y}]",
        "island_id": "ton_island",
        "description": f"Покупка участка [{x}, {y}] на TON Island",
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.transactions.insert_one(tx)
    
    logger.info(f"Plot purchased: ({x},{y}) by {user.get('username')} for {price} TON")
    
    return {
        "status": "purchased",
        "plot": plot,
        "new_balance": user.get("balance_ton", 0) - price
    }

@api_router.post("/island/build/{x}/{y}")
async def build_on_island(x: int, y: int, request: dict, current_user: User = Depends(get_current_user)):
    """Build a business on owned plot"""
    business_type = request.get("business_type")
    if not business_type:
        raise HTTPException(status_code=400, detail="business_type is required")
    
    # Get plot
    plot = await db.plots.find_one({"island_id": "ton_island", "x": x, "y": y}, {"_id": 0})
    if not plot:
        raise HTTPException(status_code=404, detail="Участок не найден")
    
    # Verify ownership - search by email or wallet
    user = None
    if current_user.wallet_address:
        user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if not user and current_user.email:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_id = user.get("id", str(user.get("_id")))
    
    if plot["owner"] != user_id and plot["owner"] != current_user.wallet_address:
        raise HTTPException(status_code=403, detail="Это не ваш участок")
    
    if plot.get("business"):
        raise HTTPException(status_code=400, detail="На участке уже есть бизнес")
    
    # Validate business type
    biz_config = BUSINESSES.get(business_type)
    if not biz_config:
        raise HTTPException(status_code=400, detail="Неизвестный тип бизнеса")
    
    # Check zone restrictions
    island = await db.islands.find_one({"id": "ton_island"}, {"_id": 0})
    cell = None
    for c in island["cells"]:
        if c["x"] == x and c["y"] == y:
            cell = c
            break
    
    zone_config = ZONES.get(cell["zone"], {})
    if biz_config["tier"] not in zone_config.get("tier_allowed", [1, 2, 3]):
        raise HTTPException(
            status_code=400, 
            detail=f"Бизнес Tier {biz_config['tier']} нельзя построить в зоне {cell['zone']}"
        )
    
    # Check cost
    build_cost = biz_config["base_cost_ton"]
    if user.get("balance_ton", 0) < build_cost:
        raise HTTPException(status_code=400, detail="Недостаточно средств для строительства")
    
    # Create business with full structure
    tier = biz_config.get("tier", 1)
    produces = biz_config.get("produces")
    production_rate = biz_config.get("production_rate", 0)
    tier_names = {1: "small", 2: "medium", 3: "large"}
    
    business = {
        "id": str(uuid.uuid4()),
        "island_id": "ton_island",
        "plot_id": plot["id"],
        "x": x,
        "y": y,
        "zone": cell["zone"],  # Zone where business is located
        "business_type": business_type,
        "name": biz_config.get("name", {}).get("ru", business_type),
        "tier": tier,
        "tier_name": tier_names.get(tier, "small"),  # small/medium/large
        "level": 1,
        "durability": 100.0,  # 100% health
        "xp": 0,
        "owner": user_id,  # Use consistent user ID
        "owner_wallet": current_user.wallet_address,
        "owner_username": user.get("username"),
        "patron": None,  # No patron initially
        "patron_id": None,
        "last_patron_change": None,
        "produces": produces,  # What this business produces
        "production_rate": production_rate,  # Base production per tick
        "consumes": biz_config.get("consumes", []),  # What it consumes
        "status": "working",  # working, stopped, on_sale
        "storage": {
            "capacity": get_storage_capacity(business_type, 1),
            "items": {}
        },
        "pending_income": 0,
        "last_collection": datetime.now(timezone.utc).isoformat(),
        "last_wear_update": datetime.now(timezone.utc).isoformat(),
        "last_tick": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.businesses.insert_one(business.copy())
    
    # Update plot
    await db.plots.update_one(
        {"id": plot["id"]},
        {"$set": {"business": business_type}}
    )
    
    # Deduct cost - search by email or id
    user_filter = {"email": user.get("email")} if user.get("email") else {"id": user_id}
    await db.users.update_one(
        user_filter,
        {"$inc": {"balance_ton": -build_cost}}
    )
    
    # Record transaction for history
    biz_name = biz_config.get("name", {}).get("ru") or business_type
    tx = {
        "id": str(uuid.uuid4()),
        "type": "business_build",
        "user_id": user_id,
        "amount_ton": -build_cost,
        "business_id": business["id"],
        "business_type": business_type,
        "plot_coords": f"[{x}, {y}]",
        "description": f"Строительство бизнеса {biz_name} на [{x}, {y}]",
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.transactions.insert_one(tx)
    
    logger.info(f"Business built: {business_type} at ({x},{y}) by {user.get('username')}")
    
    return {
        "status": "built",
        "business": business,
        "business_id": business["id"],
        "new_balance": user.get("balance_ton", 0) - build_cost
    }

# ==================== BUSINESS MANAGEMENT ROUTES ====================

from game_systems import (
    PatronageSystem, BusinessEconomics, WarehouseSystem, 
    BankingSystem, TaxSystem, IncomeCollector
)

@api_router.get("/business/{business_id}")
async def get_business_details(business_id: str, current_user: User = Depends(get_current_user)):
    """Get detailed business information"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Бизнес не найден")
    
    # Get patron info if exists
    patron_info = None
    patron_bonus = 1.0
    if business.get("patron_id"):
        patron_biz = await db.businesses.find_one({"id": business["patron_id"]}, {"_id": 0})
        if patron_biz:
            patron_type = PatronageSystem.get_patron_type(patron_biz.get("business_type"))
            patron_info = {
                "id": patron_biz["id"],
                "owner": patron_biz.get("owner"),
                "type": patron_type,
                "level": patron_biz.get("level", 1),
                "bonus_type": PATRON_BONUSES.get(patron_type, {}).get("type"),
            }
            patron_bonus = PatronageSystem.get_patron_bonus_multiplier(
                patron_type, patron_biz.get("level", 1), "income"
            )
    
    # Calculate current production
    production = BusinessEconomics.calculate_effective_production(business, patron_bonus)
    
    # Calculate pending income
    pending = IncomeCollector.calculate_pending_income(business, patron_bonus)
    
    # Get upgrade info
    can_upgrade, upgrade_cost = BusinessEconomics.can_upgrade(business)
    
    # Get repair cost
    repair_cost = BusinessEconomics.get_repair_cost(business)
    
    # Business config
    config = BUSINESSES.get(business.get("business_type"), {})
    
    return {
        "business": {
            **business,
            "config": {
                "name": config.get("name"),
                "tier": config.get("tier"),
                "icon": config.get("icon"),
                "produces": config.get("produces"),
                "consumes": config.get("consumes", []),
                "is_patron": config.get("is_patron", False),
            }
        },
        "patron": patron_info,
        "production": production,
        "pending_income": pending,
        "upgrade": {
            "can_upgrade": can_upgrade,
            "next_level": business.get("level", 1) + 1 if can_upgrade else None,
            "cost": upgrade_cost
        },
        "repair": repair_cost
    }

@api_router.post("/business/{business_id}/upgrade")
async def upgrade_business(business_id: str, current_user: User = Depends(get_current_user)):
    """Upgrade business to next level"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Бизнес не найден")
    
    ui = await get_user_identifiers(current_user)
    if not ui["user"] or not is_owner(business, ui["ids"]):
        raise HTTPException(status_code=403, detail="Это не ваш бизнес")
    user = ui["user"]
    
    can_upgrade, cost = BusinessEconomics.can_upgrade(business)
    if not can_upgrade:
        raise HTTPException(status_code=400, detail="Достигнут максимальный уровень")
    
    if user.get("balance_ton", 0) < cost["ton"]:
        raise HTTPException(status_code=400, detail="Недостаточно TON для улучшения")
    
    # Check resource if needed
    if cost.get("resource_type") and cost.get("resource_amount", 0) > 0:
        current_resource = business.get("storage", {}).get("items", {}).get(cost["resource_type"], 0)
        if current_resource < cost["resource_amount"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Недостаточно {cost['resource_type']}: нужно {cost['resource_amount']}, есть {current_resource}"
            )
    
    # Apply upgrade
    upgrade_data = BusinessEconomics.upgrade_business(business)
    
    # Update business
    await db.businesses.update_one(
        {"id": business_id},
        {"$set": upgrade_data}
    )
    
    # Deduct cost
    await db.users.update_one(
        get_user_filter(user),
        {"$inc": {"balance_ton": -cost["ton"]}}
    )
    
    # Deduct resources if needed
    if cost.get("resource_type") and cost.get("resource_amount", 0) > 0:
        await db.businesses.update_one(
            {"id": business_id},
            {"$inc": {f"storage.items.{cost['resource_type']}": -cost["resource_amount"]}}
        )
    
    # Record to treasury
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"upgrade_income": cost["ton"], "total_tax": cost["ton"] * 0.1}},
        upsert=True
    )
    
    logger.info(f"Business {business_id} upgraded to level {upgrade_data['level']} by {user.get('username')}")
    
    return {
        "status": "upgraded",
        "new_level": upgrade_data["level"],
        "new_capacity": upgrade_data["storage.capacity"],
        "cost_paid": cost,
        "new_balance": user.get("balance_ton", 0) - cost["ton"]
    }

@api_router.get("/business/{business_id}/upgrade-cost")
async def get_upgrade_cost(business_id: str, current_user: User = Depends(get_current_user)):
    """Get upgrade cost for business"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Бизнес не найден")
    
    can_upgrade, cost = BusinessEconomics.can_upgrade(business)
    current_level = business.get("level", 1)
    config = BUSINESSES.get(business.get("business_type"), {})
    
    return {
        "can_upgrade": can_upgrade,
        "current_level": current_level,
        "next_level": current_level + 1 if can_upgrade else None,
        "cost": cost,
        "requirements": {
            "ton": cost.get("ton", 0),
            "resource_type": cost.get("resource_type"),
            "resource_amount": cost.get("resource_amount", 0)
        } if cost else None
    }

@api_router.post("/business/{business_id}/repair")
async def repair_business(business_id: str, current_user: User = Depends(get_current_user)):
    """Repair business to full durability"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Бизнес не найден")
    
    ui = await get_user_identifiers(current_user)
    if not ui["user"] or not is_owner(business, ui["ids"]):
        raise HTTPException(status_code=403, detail="Это не ваш бизнес")
    user = ui["user"]
    
    if business.get("durability", 100) >= 100:
        raise HTTPException(status_code=400, detail="Бизнес не нуждается в ремонте")
    
    repair_info = BusinessEconomics.get_repair_cost(business)
    cost = repair_info["ton_cost"]
    
    # Check balance  
    if user.get("balance_ton", 0) < cost:
        raise HTTPException(status_code=400, detail="Недостаточно TON для ремонта")
    
    # Apply repair
    await db.businesses.update_one(
        {"id": business_id},
        {"$set": {
            "durability": 100,
            "last_wear_update": datetime.now(timezone.utc).isoformat(),
            "last_repair": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Deduct cost
    await db.users.update_one(
        get_user_filter(user),
        {"$inc": {"balance_ton": -cost}}
    )
    
    logger.info(f"Business {business_id} repaired by {user.get('username')} for {cost} TON")
    
    return {
        "status": "repaired",
        "cost_paid": cost,
        "new_durability": 100,
        "new_balance": user.get("balance_ton", 0) - cost
    }

@api_router.post("/business/{business_id}/collect")
async def collect_business_income(business_id: str, current_user: User = Depends(get_current_user)):
    """Collect accumulated income from business"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Бизнес не найден")
    
    ui = await get_user_identifiers(current_user)
    if not ui["user"] or not is_owner(business, ui["ids"]):
        raise HTTPException(status_code=403, detail="Это не ваш бизнес")
    
    # Get patron wallet if exists
    patron_wallet = None
    if business.get("patron_id"):
        patron_biz = await db.businesses.find_one({"id": business["patron_id"]}, {"_id": 0})
        if patron_biz:
            patron_wallet = patron_biz.get("owner")
    
    # Collect income
    collection = IncomeCollector.collect_income(business, patron_wallet)
    
    if collection.get("halted"):
        raise HTTPException(status_code=400, detail="Производство остановлено - нужен ремонт")
    
    if collection["collected"] <= 0:
        return {"status": "nothing_to_collect", "hours": collection["hours"]}
    
    # Update user balance
    user_filter = get_user_filter(ui["user"])
    await db.users.update_one(
        user_filter,
        {"$inc": {"balance_ton": collection["player_receives"], "total_income": collection["player_receives"]}}
    )
    
    # Update patron balance if exists
    if patron_wallet and collection["patron_receives"] > 0:
        await db.users.update_one(
            {"wallet_address": patron_wallet},
            {"$inc": {"balance_ton": collection["patron_receives"], "total_income": collection["patron_receives"]}}
        )
    
    # Update treasury
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"business_tax": collection["treasury_receives"], "total_tax": collection["treasury_receives"]}},
        upsert=True
    )
    
    # Update business last collection
    await db.businesses.update_one(
        {"id": business_id},
        {"$set": {"last_collection": datetime.now(timezone.utc).isoformat()}}
    )
    
    logger.info(f"Collected {collection['collected']} TON from business {business_id}")
    
    return {
        "status": "collected",
        "gross_income": collection["collected"],
        "player_receives": collection["player_receives"],
        "treasury_tax": collection["treasury_receives"],
        "patron_tax": collection["patron_receives"],
        "hours_accumulated": collection["hours"]
    }

# ==================== PATRONAGE ROUTES ====================

@api_router.get("/patrons")
async def get_available_patrons():
    """Get all available patron businesses"""
    patrons = await db.businesses.find(
        {"business_type": {"$in": ["validator", "gram_bank", "dex", "casino", "arena", "incubator", "bridge"]}},
        {"_id": 0}
    ).to_list(100)
    
    result = []
    for p in patrons:
        config = BUSINESSES.get(p.get("business_type"), {})
        patron_type = config.get("patron_type")
        bonus_info = PATRON_BONUSES.get(patron_type, {})
        
        owner = await db.users.find_one({"wallet_address": p.get("owner")}, {"_id": 0, "username": 1, "display_name": 1})
        
        result.append({
            "id": p["id"],
            "type": p["business_type"],
            "patron_type": patron_type,
            "level": p.get("level", 1),
            "durability": p.get("durability", 100),
            "owner": p.get("owner"),
            "owner_name": owner.get("display_name") or owner.get("username") if owner else "Unknown",
            "bonus_type": bonus_info.get("type"),
            "bonus_range": bonus_info.get("multiplier_range"),
            "current_bonus": PatronageSystem.get_patron_bonus_multiplier(patron_type, p.get("level", 1), bonus_info.get("type", "income")),
            "icon": config.get("icon"),
            "name": config.get("name")
        })
    
    return {"patrons": result}

@api_router.post("/business/{business_id}/set-patron")
async def set_business_patron(business_id: str, patron_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Set or remove patron for a business"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Бизнес не найден")
    
    ui = await get_user_identifiers(current_user)
    if not ui["user"] or not is_owner(business, ui["ids"]):
        raise HTTPException(status_code=403, detail="Это не ваш бизнес")
    
    # Check cooldown
    can_change, days_remaining = PatronageSystem.can_change_patron(business.get("last_patron_change"))
    if not can_change:
        raise HTTPException(
            status_code=400, 
            detail=f"Смена патрона доступна через {days_remaining} дней"
        )
    
    # If removing patron
    if not patron_id:
        await db.businesses.update_one(
            {"id": business_id},
            {"$set": {
                "patron_id": None,
                "last_patron_change": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {"status": "patron_removed"}
    
    # Verify patron exists and is valid
    patron = await db.businesses.find_one({"id": patron_id}, {"_id": 0})
    if not patron:
        raise HTTPException(status_code=404, detail="Патрон не найден")
    
    if not PatronageSystem.can_be_patron(patron.get("business_type")):
        raise HTTPException(status_code=400, detail="Этот бизнес не может быть патроном")
    
    # Cannot be own patron
    if patron.get("owner") == current_user.wallet_address:
        raise HTTPException(status_code=400, detail="Нельзя назначить себя патроном")
    
    await db.businesses.update_one(
        {"id": business_id},
        {"$set": {
            "patron_id": patron_id,
            "last_patron_change": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    patron_config = BUSINESSES.get(patron.get("business_type"), {})
    
    return {
        "status": "patron_set",
        "patron": {
            "id": patron_id,
            "type": patron.get("business_type"),
            "level": patron.get("level", 1),
            "owner": patron.get("owner"),
            "bonus_type": patron_config.get("patron_type")
        }
    }

# ==================== WAREHOUSE ROUTES ====================

@api_router.get("/warehouses/rentals")
async def get_warehouse_rentals():
    """Get available warehouse rentals"""
    rentals = await db.warehouse_rentals.find(
        {"status": "available"},
        {"_id": 0}
    ).to_list(50)
    
    result = []
    for r in rentals:
        owner = await db.users.find_one({"wallet_address": r.get("owner_id")}, {"_id": 0, "username": 1})
        result.append({
            **r,
            "owner_name": owner.get("username") if owner else "Unknown"
        })
    
    return {"rentals": result}

@api_router.post("/warehouses/create-rental")
async def create_warehouse_rental(
    slots: int,
    price_per_slot: float,
    current_user: User = Depends(get_current_user)
):
    """Create warehouse rental listing"""
    if slots <= 0 or price_per_slot <= 0:
        raise HTTPException(status_code=400, detail="Некорректные параметры")
    
    # Check user has warehouse capacity
    user_businesses = await db.businesses.find(
        {"owner": current_user.wallet_address},
        {"_id": 0}
    ).to_list(50)
    
    total_capacity = sum(b.get("storage", {}).get("capacity", 0) for b in user_businesses)
    total_used = sum(
        sum(b.get("storage", {}).get("items", {}).values()) 
        for b in user_businesses
    )
    
    available = total_capacity - total_used
    
    if slots > available:
        raise HTTPException(
            status_code=400, 
            detail=f"Недостаточно свободного места: доступно {available}, запрошено {slots}"
        )
    
    rental = WarehouseSystem.create_rental_offer(
        current_user.wallet_address,
        f"warehouse_{current_user.wallet_address}",
        slots,
        price_per_slot
    )
    
    await db.warehouse_rentals.insert_one(rental.copy())
    
    return {"status": "created", "rental": rental}

@api_router.post("/warehouses/rent/{rental_id}")
async def rent_warehouse(rental_id: str, days: int = 7, current_user: User = Depends(get_current_user)):
    """Rent warehouse space"""
    rental = await db.warehouse_rentals.find_one({"id": rental_id}, {"_id": 0})
    if not rental:
        raise HTTPException(status_code=404, detail="Аренда не найдена")
    
    if rental["status"] != "available":
        raise HTTPException(status_code=400, detail="Аренда недоступна")
    
    if rental["owner_id"] == current_user.wallet_address:
        raise HTTPException(status_code=400, detail="Нельзя арендовать у себя")
    
    # Calculate cost
    cost_info = WarehouseSystem.calculate_rental_cost(
        rental["slots_available"],
        rental["price_per_slot_per_day"],
        days
    )
    
    # Check balance
    user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if user.get("balance_ton", 0) < cost_info["total"]:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    
    # Process payment
    owner_receives = cost_info["base_cost"]
    
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$inc": {"balance_ton": -cost_info["total"]}}
    )
    
    await db.users.update_one(
        {"wallet_address": rental["owner_id"]},
        {"$inc": {"balance_ton": owner_receives}}
    )
    
    # Treasury tax
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"rental_tax": cost_info["tax"], "total_tax": cost_info["tax"]}},
        upsert=True
    )
    
    # Update rental
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    await db.warehouse_rentals.update_one(
        {"id": rental_id},
        {"$set": {
            "status": "rented",
            "renter_id": current_user.wallet_address,
            "rented_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat()
        }}
    )
    
    return {
        "status": "rented",
        "cost": cost_info,
        "expires_at": expires_at.isoformat(),
        "slots": rental["slots_available"]
    }

# ==================== BANKING ROUTES ====================

@api_router.get("/banks")
async def get_available_banks():
    """Get banks available for instant withdrawal"""
    banks = await db.businesses.find(
        {"business_type": "gram_bank", "durability": {"$gte": 50}},
        {"_id": 0}
    ).to_list(20)
    
    return {"banks": BankingSystem.get_available_banks(banks)}

@api_router.post("/withdraw/instant")
async def instant_withdrawal(
    amount: float,
    bank_id: str,
    current_user: User = Depends(get_current_user)
):
    """Create instant withdrawal via bank"""
    if amount < MIN_WITHDRAWAL:
        raise HTTPException(status_code=400, detail=f"Минимальная сумма вывода: {MIN_WITHDRAWAL} TON")
    
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        raise HTTPException(status_code=400, detail="Пользователь не найден")
    user = ui["user"]
    
    # Check if user has wallet connected
    wallet_address = user.get("wallet_address")
    if not wallet_address:
        raise HTTPException(status_code=400, detail="Подключите кошелёк для вывода средств")
    
    balance = user.get("balance_ton", 0)
    if balance < amount:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    
    # Check credit restriction
    or_conds = [{"borrower_id": uid} for uid in ui["ids"]]
    or_conds.extend([{"borrower_wallet": uid} for uid in ui["ids"]])
    active_credits = await db.credits.find(
        {"$or": or_conds, "status": {"$in": ["active", "overdue"]}},
        {"_id": 0}
    ).to_list(20)
    
    total_debt = sum(c.get("remaining_amount") or c.get("remaining") or 0 for c in active_credits)
    available = balance - total_debt
    
    if available < amount:
        if available <= 0:
            raise HTTPException(status_code=400, detail=f"Вывод заблокирован: ваш долг ({total_debt:.2f} TON) превышает баланс. Погасите кредит.")
        raise HTTPException(status_code=400, detail=f"Максимальная сумма вывода: {available:.2f} TON (баланс {balance:.2f} - долг {total_debt:.2f})")
    
    # Verify bank
    bank = await db.businesses.find_one({"id": bank_id}, {"_id": 0})
    can_process, reason = BankingSystem.can_process_instant(bank, amount)
    
    if not can_process:
        error_msgs = {
            "no_bank_selected": "Банк не выбран",
            "not_a_bank": "Это не банк",
            "bank_durability_low": "Прочность банка ниже 50%"
        }
        raise HTTPException(status_code=400, detail=error_msgs.get(reason, "Ошибка банка"))
    
    # Create withdrawal
    withdrawal = BankingSystem.create_withdrawal_request(
        wallet_address,
        amount,
        "instant"
    )
    withdrawal["bank_id"] = bank_id
    withdrawal["bank_owner"] = bank.get("owner")
    
    # Deduct from user
    user_filter = get_user_filter(user)
    await db.users.update_one(
        user_filter,
        {"$inc": {"balance_ton": -amount}}
    )
    
    # Pay bank fee to bank owner
    bank_fee = withdrawal["bank_fee"]
    await db.users.update_one(
        {"wallet_address": bank.get("owner")},
        {"$inc": {"balance_ton": bank_fee, "total_income": bank_fee}}
    )
    
    # Store withdrawal
    await db.transactions.insert_one({**withdrawal, "tx_type": "instant_withdrawal"})
    
    return {
        "status": "pending",
        "withdrawal_id": withdrawal["id"],
        "type": "instant",
        "amount": amount,
        "net_amount": withdrawal["net_amount"],
        "bank_fee": bank_fee,
        "platform_commission": withdrawal["platform_commission"]
    }

@api_router.get("/withdrawals/queue")
async def get_withdrawal_queue(current_user: User = Depends(get_current_user)):
    """Get user's withdrawal queue"""
    withdrawals = await db.transactions.find(
        {
            "user_wallet": current_user.wallet_address,
            "tx_type": {"$in": ["withdrawal", "instant_withdrawal"]}
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    
    return {"withdrawals": withdrawals}

# ==================== MY BUSINESSES ROUTES ====================

@api_router.get("/my/businesses")
async def get_my_businesses_full(current_user: User = Depends(get_current_user)):
    """Get all user's businesses with full details"""
    # Search using unified helper
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        return {"businesses": [], "summary": {"total_businesses": 0, "total_pending_income": 0, "total_hourly_income": 0, "total_daily_income": 0}}
    
    query = get_businesses_query(ui["ids"])
    businesses = await db.businesses.find(query, {"_id": 0}).to_list(50)
    
    # Calculate shared warehouse totals
    total_warehouse_capacity = 0
    total_warehouse_used = 0
    
    result = []
    total_pending = 0
    total_hourly = 0
    
    for biz in businesses:
        config = BUSINESSES.get(biz.get("business_type"), {})
        
        # Get patron bonus if exists
        patron_bonus = 1.0
        patron_info = None
        if biz.get("patron_id"):
            patron = await db.businesses.find_one({"id": biz["patron_id"]}, {"_id": 0})
            if patron:
                patron_type = PatronageSystem.get_patron_type(patron.get("business_type"))
                patron_bonus = PatronageSystem.get_patron_bonus_multiplier(
                    patron_type, patron.get("level", 1), "income"
                )
                patron_info = {"id": patron["id"], "type": patron_type, "level": patron.get("level", 1)}
        
        # Calculate production
        production = BusinessEconomics.calculate_effective_production(biz, patron_bonus)
        pending = IncomeCollector.calculate_pending_income(biz, patron_bonus)
        
        total_pending += pending.get("pending", 0)
        total_hourly += production.get("income_after_tax", 0)
        
        # Storage info
        storage = biz.get("storage", {})
        capacity = storage.get("capacity", 0)
        items = storage.get("items", {})
        used = sum(int(v) for v in items.values() if v > 0)
        total_warehouse_capacity += capacity
        total_warehouse_used += used
        
        # Working/Idle status
        is_storage_full = (used >= capacity) if capacity > 0 else False
        durability = biz.get("durability", 100)
        is_halted = durability <= 0 or production.get("status") == "halted"
        
        if is_halted:
            work_status = "halted"
            work_status_reason = "durability_zero" if durability <= 0 else "no_resources"
        elif is_storage_full:
            work_status = "idle"
            work_status_reason = "storage_full"
        else:
            work_status = "working"
            work_status_reason = None
        
        result.append({
            **biz,
            "config": {
                "name": config.get("name"),
                "tier": config.get("tier"),
                "icon": config.get("icon"),
                "produces": config.get("produces"),
            },
            "production": production,
            "pending_income": pending.get("pending", 0),
            "patron": patron_info,
            "storage_info": {
                "capacity": capacity,
                "used": used,
                "items": items,
                "is_full": is_storage_full,
            },
            "work_status": work_status,
            "work_status_reason": work_status_reason,
        })
    
    return {
        "businesses": result,
        "summary": {
            "total_businesses": len(result),
            "total_pending_income": round(total_pending, 4),
            "total_hourly_income": round(total_hourly, 6),
            "total_daily_income": round(total_hourly * 24, 4),
            "total_warehouse_capacity": total_warehouse_capacity,
            "total_warehouse_used": total_warehouse_used,
        }
    }

@api_router.post("/my/collect-all")
async def collect_all_income(current_user: User = Depends(get_current_user)):
    """Collect income from all businesses"""
    # Search by both user.id and wallet_address for compatibility
    query = {"$or": [
        {"owner": current_user.id},
        {"owner": current_user.wallet_address}
    ]} if current_user.wallet_address else {"owner": current_user.id}
    
    businesses = await db.businesses.find(query, {"_id": 0}).to_list(50)
    
    total_collected = 0
    total_tax = 0
    total_patron = 0
    collected_count = 0
    
    for biz in businesses:
        patron_wallet = None
        if biz.get("patron_id"):
            patron = await db.businesses.find_one({"id": biz["patron_id"]}, {"_id": 0})
            if patron:
                patron_wallet = patron.get("owner")
        
        collection = IncomeCollector.collect_income(biz, patron_wallet)
        
        if collection.get("halted") or collection["collected"] <= 0:
            continue
        
        total_collected += collection["player_receives"]
        total_tax += collection["treasury_receives"]
        total_patron += collection["patron_receives"]
        collected_count += 1
        
        # Update business
        await db.businesses.update_one(
            {"id": biz["id"]},
            {"$set": {"last_collection": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Pay patron
        if patron_wallet and collection["patron_receives"] > 0:
            await db.users.update_one(
                {"wallet_address": patron_wallet},
                {"$inc": {"balance_ton": collection["patron_receives"]}}
            )
    
    # Update user - search by id or wallet_address
    if total_collected > 0:
        user_query = {"$or": [{"id": current_user.id}]}
        if current_user.wallet_address:
            user_query["$or"].append({"wallet_address": current_user.wallet_address})
        await db.users.update_one(
            user_query,
            {"$inc": {"balance_ton": total_collected, "total_income": total_collected}}
        )
    
    # Update treasury
    if total_tax > 0:
        await db.admin_stats.update_one(
            {"type": "treasury"},
            {"$inc": {"business_tax": total_tax, "total_tax": total_tax}},
            upsert=True
        )
    
    return {
        "status": "collected",
        "businesses_collected": collected_count,
        "total_player_income": round(total_collected, 4),
        "total_tax_paid": round(total_tax, 4),
        "total_patron_fees": round(total_patron, 4)
    }

# ==================== CITIES ROUTES ====================

from city_generator import create_demo_cities, calculate_plot_price_in_city

@api_router.get("/cities")
async def get_all_cities():
    """Get all cities with basic info for map view"""
    cities = await db.cities.find({}, {"_id": 0}).to_list(100)
    
    if not cities:
        # Seed demo cities if none exist
        demo_cities = create_demo_cities()
        for city in demo_cities:
            await db.cities.insert_one(city.copy())
        cities = demo_cities
    
    # Return lightweight version for list view
    result = []
    for city in cities:
        # Update stats from actual data
        owned_plots = await db.plots.count_documents({"city_id": city["id"], "owner": {"$ne": None}})
        total_businesses = await db.businesses.count_documents({"city_id": city["id"]})
        
        # Handle localized name - convert to string
        city_name = city.get("name", "Unknown")
        if isinstance(city_name, dict):
            city_name = city_name.get("ru") or city_name.get("en") or "Unknown"
        
        city_desc = city.get("description", "")
        if isinstance(city_desc, dict):
            city_desc = city_desc.get("ru") or city_desc.get("en") or ""
        
        result.append({
            "id": city["id"],
            "name": city_name,
            "description": city_desc,
            "style": city["style"],
            "base_price": city["base_price"],
            "grid_preview": city["grid"],  # For silhouette rendering
            "stats": {
                "total_plots": city["stats"]["total_plots"],
                "owned_plots": owned_plots,
                "total_businesses": total_businesses,
                "monthly_volume": city["stats"].get("monthly_volume", 0),
                "active_players": city["stats"].get("active_players", 0)
            }
        })
    
    return {"cities": result, "total": len(result)}

@api_router.get("/cities/{city_id}")
async def get_city(city_id: str):
    """Get full city data including grid"""
    city = await db.cities.find_one({"id": city_id}, {"_id": 0})
    
    if not city:
        raise HTTPException(status_code=404, detail="Город не найден")
    
    return city

@api_router.get("/cities/{city_id}/plots")
async def get_city_plots(city_id: str):
    """Get all plots for a specific city"""
    city = await db.cities.find_one({"id": city_id}, {"_id": 0})
    if not city:
        raise HTTPException(status_code=404, detail="Город не найден")
    
    # Get existing plots
    plots = await db.plots.find({"city_id": city_id}, {"_id": 0}).to_list(10000)
    plots_map = {f"{p['x']}_{p['y']}": p for p in plots}
    
    # Get businesses
    businesses = await db.businesses.find({"city_id": city_id}, {"_id": 0}).to_list(10000)
    business_map = {b["plot_id"]: b for b in businesses}
    
    # Generate full plot list from grid
    grid = city["grid"]
    result = []
    
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == 1:  # Land cell
                plot_key = f"{x}_{y}"
                existing_plot = plots_map.get(plot_key)
                
                if existing_plot:
                    business = business_map.get(existing_plot.get("id"))
                    bt = BUSINESS_TYPES.get(business["business_type"]) if business else None
                    result.append({
                        "id": existing_plot["id"],
                        "x": x,
                        "y": y,
                        "city_id": city_id,
                        "owner": existing_plot.get("owner"),
                        "price": existing_plot.get("price", calculate_plot_price_in_city(city, x, y)),
                        "is_available": existing_plot.get("is_available", True),
                        "business_id": existing_plot.get("business_id"),
                        "business_type": business["business_type"] if business else None,
                        "business_icon": bt["icon"] if bt else None,
                        "business_level": business.get("level", 1) if business else None
                    })
                else:
                    # Plot doesn't exist yet in DB - create virtual entry
                    result.append({
                        "id": None,
                        "x": x,
                        "y": y,
                        "city_id": city_id,
                        "owner": None,
                        "price": calculate_plot_price_in_city(city, x, y),
                        "is_available": True,
                        "business_id": None,
                        "business_type": None,
                        "business_icon": None,
                        "business_level": None
                    })
    
    return {"plots": result, "total": len(result), "city": {"id": city_id, "name": city["name"], "style": city["style"]}}

@api_router.post("/cities/{city_id}/plots/{x}/{y}/buy")
async def buy_city_plot(city_id: str, x: int, y: int, current_user: User = Depends(get_current_user)):
    """Buy a plot in a specific city"""
    city = await db.cities.find_one({"id": city_id}, {"_id": 0})
    if not city:
        raise HTTPException(status_code=404, detail="Город не найден")
    
    # Check if coordinates are valid (within grid and is land)
    grid = city["grid"]
    if y < 0 or y >= len(grid) or x < 0 or x >= len(grid[0]) or grid[y][x] != 1:
        raise HTTPException(status_code=400, detail="Неверные координаты участка")
    
    # Check if plot already owned
    existing_plot = await db.plots.find_one({"city_id": city_id, "x": x, "y": y})
    if existing_plot and existing_plot.get("owner"):
        raise HTTPException(status_code=400, detail="Участок уже куплен другим игроком")
    
    # Get user
    user = await db.users.find_one({"$or": [
        {"wallet_address": current_user.wallet_address},
        {"email": current_user.email},
        {"username": current_user.username}
    ]})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Check plot limit - 3 plots max for regular users, unlimited for admins and banks
    is_admin = user.get("is_admin", False) or user.get("role") == "ADMIN"
    is_bank = user.get("is_bank", False) or user.get("role") == "BANK"
    
    if not is_admin and not is_bank:
        user_plots = len(user.get("plots_owned", []))
        max_plots = 3  # Fixed limit of 3 plots for all regular users
        if user_plots >= max_plots:
            raise HTTPException(status_code=400, detail=t("max_plots_reached", user.get("language", "en")))
    
    # Calculate price
    price = calculate_plot_price_in_city(city, x, y)
    
    # Check balance
    if user.get("balance_ton", 0) < price:
        raise HTTPException(status_code=400, detail="Недостаточно TON на балансе")
    
    # Create or update plot
    plot_id = f"{city_id}_{x}_{y}"
    # Используем user.id как основной идентификатор
    user_id = user.get("id", str(user.get("_id")))
    
    plot_data = {
        "id": plot_id,
        "city_id": city_id,
        "x": x,
        "y": y,
        "price": price,
        "owner": user_id,
        "owner_username": user.get("username"),
        "owner_avatar": user.get("avatar"),
        "is_available": False,
        "purchased_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.plots.update_one(
        {"city_id": city_id, "x": x, "y": y},
        {"$set": plot_data},
        upsert=True
    )
    
    # Update user by id field
    new_balance = user.get("balance_ton", 0) - price
    await db.users.update_one(
        {"id": user_id},
        {
            "$inc": {"balance_ton": -price},
            "$push": {"plots_owned": plot_id}
        }
    )
    
    # Record transaction in history
    import uuid as uuid_module
    history_tx = {
        "id": str(uuid_module.uuid4()),
        "user_id": user_id,
        "type": "land_purchase",
        "amount": -price,
        "details": {
            "plot_id": plot_id,
            "city_id": city_id,
            "x": x,
            "y": y,
            "price": price
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.transactions.insert_one(history_tx)
    
    return {"status": "success", "plot": plot_data, "new_balance": new_balance}

@api_router.post("/cities/{city_id}/plots/{x}/{y}/build")
async def build_business_in_city(city_id: str, x: int, y: int, request: dict, current_user: User = Depends(get_current_user)):
    """Build a business on owned plot in a city"""
    business_type = request.get("business_type")
    
    if not business_type or business_type not in BUSINESS_TYPES:
        raise HTTPException(status_code=400, detail="Неверный тип бизнеса")
    
    bt = BUSINESS_TYPES[business_type]
    
    # Find the plot
    plot = await db.plots.find_one({"city_id": city_id, "x": x, "y": y})
    if not plot:
        raise HTTPException(status_code=404, detail="Участок не найден")
    
    # Get user
    user = await db.users.find_one({"$or": [
        {"wallet_address": current_user.wallet_address},
        {"email": current_user.email},
        {"username": current_user.username}
    ]})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Check ownership - use consistent user ID logic
    user_id = user.get("id", str(user.get("_id")))
    if plot.get("owner") != user_id:
        raise HTTPException(status_code=403, detail="You don't own this plot")
    
    # Check if business already exists
    if plot.get("business_id"):
        raise HTTPException(status_code=400, detail="Бизнес уже существует на этом участке")
    
    # Check balance
    build_cost = bt["cost"]
    if user.get("balance_ton", 0) < build_cost:
        raise HTTPException(status_code=400, detail="Недостаточно TON на балансе")
    
    # Create business
    business_id = f"biz_{city_id}_{x}_{y}"
    business_data = {
        "id": business_id,
        "city_id": city_id,
        "plot_id": plot["id"],
        "plot_x": x,
        "plot_y": y,
        "business_type": business_type,
        "owner": user_id,  # Use consistent user ID
        "owner_username": user.get("username"),
        "level": 1,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "last_collection": datetime.now(timezone.utc).isoformat(),
        "total_income": 0,
        "status": "active"
    }
    
    await db.businesses.insert_one(business_data.copy())
    
    # Update plot
    await db.plots.update_one(
        {"city_id": city_id, "x": x, "y": y},
        {"$set": {"business_id": business_id, "business_type": business_type}}
    )
    
    # Update user
    await db.users.update_one(
        {"id": user_id},  # Use consistent user ID field
        {
            "$inc": {"balance_ton": -build_cost},
            "$push": {"businesses_owned": business_id}
        }
    )
    
    return {
        "status": "success", 
        "business": {
            "id": business_id,
            "type": business_type,
            "icon": bt["icon"],
            "name": bt["name"]
        },
        "new_balance": user.get("balance_ton", 0) - build_cost
    }

# ==================== PLOTS ROUTES (Legacy) ====================

@api_router.get("/plots")
async def get_all_plots():
    """Get all plots with ownership info"""
    plots = await db.plots.find({}, {"_id": 0}).to_list(10000)
    businesses = await db.businesses.find({}, {"_id": 0}).to_list(10000)
    business_map = {b["plot_id"]: b for b in businesses}
    
    result = []
    for plot in plots:
        business = business_map.get(plot["id"])
        bt = BUSINESS_TYPES.get(business["business_type"]) if business else None
        result.append({
            "id": plot["id"],
            "x": plot["x"],
            "y": plot["y"],
            "zone": plot.get("zone", "outskirts"),
            "owner": plot.get("owner"),
            "price": plot["price"],
            "is_available": plot.get("is_available", True),
            "is_rented": plot.get("is_rented", False),
            "rent_price": plot.get("rent_price"),
            "business_id": plot.get("business_id"),
            "business_type": business["business_type"] if business else None,
            "business_icon": bt["icon"] if bt else None,
            "business_level": business.get("level", 1) if business else None
        })
    
    return {"plots": result, "total": len(result)}

@api_router.get("/plots/coords/{x}/{y}")
async def get_plot_by_coords(x: int, y: int):
    """Get plot by coordinates with owner info"""
    plot = await db.plots.find_one({"x": x, "y": y}, {"_id": 0})
    
    if not plot:
        price, zone = calculate_plot_price(x, y)
        new_plot = Plot(x=x, y=y, price=price, zone=zone)
        plot_dict = new_plot.model_dump()
        await db.plots.insert_one(plot_dict.copy())
        plot = await db.plots.find_one({"x": x, "y": y}, {"_id": 0})
    
    business = None
    if plot.get("business_id"):
        business = await db.businesses.find_one({"id": plot["business_id"]}, {"_id": 0})
    
    # Get owner info if plot is owned
    owner_info = None
    if plot.get("owner"):
        owner = await db.users.find_one(
            {"$or": [{"wallet_address": plot["owner"]}, {"id": plot.get("owner_id")}]},
            {"_id": 0, "hashed_password": 0, "two_factor_secret": 0, "backup_codes": 0}
        )
        if owner:
            owner_info = {
                "id": owner.get("id"),
                "username": owner.get("username"),
                "display_name": owner.get("display_name") or owner.get("username"),
                "avatar": owner.get("avatar"),
                "level": owner.get("level", 1)
            }
    
    return {
        **plot,
        "business": business,
        "business_info": BUSINESS_TYPES.get(business["business_type"]) if business else None,
        "owner_info": owner_info
    }

@api_router.post("/plots/purchase")
async def purchase_plot(request: PurchasePlotRequest, current_user: User = Depends(get_current_user)):
    """Purchase plot using internal balance"""
    x, y = request.plot_x, request.plot_y
    lang = current_user.language
    
    # Check player limits
    # Check plot limit - 3 plots max for regular users, unlimited for admins and banks
    is_admin = current_user.is_admin or current_user.role == "ADMIN"
    is_bank = getattr(current_user, 'is_bank', False) or current_user.role == "BANK"
    
    if not is_admin and not is_bank:
        max_plots = 3  # Fixed limit of 3 plots for all regular users
        if len(current_user.plots_owned) >= max_plots:
            raise HTTPException(status_code=400, detail=t("max_plots_reached", lang))
    
    plot = await db.plots.find_one({"x": x, "y": y}, {"_id": 0})
    
    if not plot:
        price, zone = calculate_plot_price(x, y)
        new_plot = Plot(x=x, y=y, price=price, zone=zone)
        plot_dict = new_plot.model_dump()
        await db.plots.insert_one(plot_dict.copy())
        plot = await db.plots.find_one({"x": x, "y": y}, {"_id": 0})
    
    if not plot.get("is_available", True):
        raise HTTPException(status_code=400, detail=t("plot_not_available", lang))
    
    # Check balance
    plot_price = plot["price"]
    if current_user.balance_ton < plot_price:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance. Need {plot_price} TON, have {current_user.balance_ton} TON"
        )
    
    # Check zone limits
    zone = plot.get("zone", "outskirts")
    zone_limit = ZONES.get(zone, {}).get("plot_limit", 30)
    user_plots_in_zone = await db.plots.count_documents({
        "owner": current_user.wallet_address,
        "zone": zone
    })
    if user_plots_in_zone >= zone_limit:
        raise HTTPException(status_code=400, detail=f"Zone limit reached for {zone}")
    
    # Deduct from internal balance
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$inc": {"balance_ton": -plot_price}}
    )
    
    # Update plot owner
    await db.plots.update_one(
        {"id": plot["id"]},
        {
            "$set": {
                "owner": current_user.wallet_address,
                "owner_id": current_user.id,
                "owner_avatar": current_user.avatar,
                "owner_username": current_user.username,
                "is_available": False,
                "purchased_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Update user plots
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$push": {"plots_owned": plot["id"]}}
    )
    
    # Record transaction
    tx = Transaction(
        tx_type="purchase_plot",
        from_address=current_user.wallet_address,
        to_address="admin_treasury",
        amount_ton=plot_price,
        plot_id=plot["id"],
        status="completed"
    )
    tx_dict = tx.model_dump()
    tx_dict['created_at'] = tx_dict['created_at'].isoformat()
    await db.transactions.insert_one(tx_dict.copy())
    
    # Record in user transaction history
    import uuid as uuid_module
    history_tx = {
        "id": str(uuid_module.uuid4()),
        "user_id": current_user.id,
        "type": "land_purchase",
        "amount": -plot_price,
        "details": {
            "plot_id": plot["id"],
            "plot_x": x,
            "plot_y": y,
            "zone": zone,
            "price": plot_price
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.transactions.insert_one(history_tx)
    
    # Record admin income
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {
            "$inc": {
                "plot_sales_income": plot_price,
                "total_plot_sales": 1
            }
        },
        upsert=True
    )
    
    logger.info(f"Plot ({x}, {y}) purchased by {current_user.wallet_address} for {plot_price} TON")
    
    return {
        "success": True,
        "plot_id": plot["id"],
        "amount_paid": plot_price,
        "new_balance": current_user.balance_ton - plot_price,
        "message": f"Plot ({x}, {y}) purchased successfully!"
    }

@api_router.post("/plots/confirm-purchase")
async def confirm_plot_purchase(request: ConfirmTransactionRequest, current_user: User = Depends(get_current_user)):
    """Confirm plot purchase"""
    tx = await db.transactions.find_one({"id": request.transaction_id}, {"_id": 0})
    
    if not tx or tx["from_address"] != current_user.wallet_address:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    
    if tx["status"] == "completed":
        raise HTTPException(status_code=400, detail="Транзакция уже завершена")
    
    # Update transaction
    await db.transactions.update_one(
        {"id": request.transaction_id},
        {"$set": {"status": "completed", "blockchain_hash": request.blockchain_hash, 
                  "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update plot
    await db.plots.update_one(
        {"id": tx["plot_id"]},
        {"$set": {"owner": current_user.wallet_address, "is_available": False,
                  "purchased_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update user
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$push": {"plots_owned": tx["plot_id"]},
         "$inc": {"total_turnover": tx["amount_ton"]}}
    )
    
    # Update admin stats
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"total_plot_sales": tx["amount_ton"], "total_income": tx["amount_ton"]}},
        upsert=True
    )
    
    # Broadcast update
    await manager.broadcast({"type": "plot_sold", "plot_id": tx["plot_id"], "owner": current_user.wallet_address})
    
    return {"status": "completed", "plot_id": tx["plot_id"], "message": t("plot_purchased", current_user.language)}

@api_router.post("/plots/resale")
async def resale_plot(request: ResalePlotRequest, current_user: User = Depends(get_current_user)):
    """List plot for resale with minimum price rules"""
    plot = await db.plots.find_one({"id": request.plot_id}, {"_id": 0})
    
    if not plot or plot.get("owner") != current_user.wallet_address:
        raise HTTPException(status_code=404, detail="Plot not found or not owned")
    
    # Calculate original plot price
    original_price = calculate_plot_price(plot["x"], plot["y"])
    min_plot_price = original_price * 0.5  # 50% of original
    
    # If plot has business, cannot sell (must demolish first or include in price)
    business = None
    if plot.get("business_id"):
        business = await db.businesses.find_one({"id": plot["business_id"]}, {"_id": 0})
        if business:
            # Get business cost
            business_config = BUSINESS_TYPES.get(business["business_type"], {})
            business_cost = business_config.get("cost", 0)
            level = business.get("level", 1)
            
            # Calculate total business investment
            total_business_cost = business_cost
            for lvl in range(2, level + 1):
                upgrade_cost = LEVEL_CONFIG.get(lvl, {}).get("upgrade_cost", 0)
                total_business_cost += upgrade_cost
            
            # Minimum price = plot price + half of business value
            min_plot_price = original_price + (total_business_cost * 0.5)
    
    # Check minimum price
    if request.price < min_plot_price:
        raise HTTPException(
            status_code=400, 
            detail=f"Price too low. Minimum price: {min_plot_price} TON (50% of original value{' + half of business value' if business else ''})"
        )
    
    await db.plots.update_one(
        {"id": request.plot_id},
        {"$set": {
            "is_available": True, 
            "price": request.price, 
            "is_resale": True,
            "original_price": original_price,
            "has_business": bool(business)
        }}
    )
    
    return {
        "status": "listed", 
        "plot_id": request.plot_id, 
        "price": request.price,
        "min_price": min_plot_price,
        "has_business": bool(business)
    }

@api_router.post("/plots/buy-resale/{plot_id}")
async def buy_resale_plot(plot_id: str, current_user: User = Depends(get_current_user)):
    """Buy a resale plot with 15% tax"""
    plot = await db.plots.find_one({"id": plot_id}, {"_id": 0})
    
    if not plot or not plot.get("is_resale"):
        raise HTTPException(status_code=404, detail="Участок не выставлен на продажу")
    
    if plot["owner"] == current_user.wallet_address:
        raise HTTPException(status_code=400, detail="Нельзя купить свой собственный участок")
    
    seller_address = plot["owner"]
    price = plot["price"]
    commission = price * RESALE_COMMISSION  # 15% tax
    seller_amount = price - commission
    
    # Check buyer balance
    buyer = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if buyer["balance_ton"] < price:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Need {price} TON")
    
    # Transfer ownership
    await db.plots.update_one(
        {"id": plot_id},
        {"$set": {
            "owner": current_user.wallet_address,
            "is_available": False,
            "is_resale": False,
            "price": plot.get("original_price", price)  # Reset to original price
        }}
    )
    
    # Update buyer balance
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$inc": {"balance_ton": -price}, "$push": {"plots_owned": f"{plot['x']},{plot['y']}"}}
    )
    
    # Update seller balance
    await db.users.update_one(
        {"wallet_address": seller_address},
        {"$inc": {"balance_ton": seller_amount}, "$pull": {"plots_owned": f"{plot['x']},{plot['y']}"}}
    )
    
    # If plot has business, transfer it too
    if plot.get("business_id"):
        await db.businesses.update_one(
            {"id": plot["business_id"]},
            {"$set": {"owner": current_user.wallet_address}}
        )
        
        # Update business ownership lists
        await db.users.update_one(
            {"wallet_address": seller_address},
            {"$pull": {"businesses_owned": plot["business_id"]}}
        )
        await db.users.update_one(
            {"wallet_address": current_user.wallet_address},
            {"$push": {"businesses_owned": plot["business_id"]}}
        )
    
    # Add commission to treasury
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"resale_tax": commission, "total_income": commission}},
        upsert=True
    )
    
    # Record transaction
    tx = Transaction(
        tx_type="resale_plot",
        from_address=current_user.wallet_address,
        to_address=seller_address,
        amount_ton=price,
        commission=commission,
        plot_id=plot_id
    )
    tx_dict = tx.model_dump()
    tx_dict['created_at'] = tx_dict['created_at'].isoformat()
    await db.transactions.insert_one(tx_dict.copy())
    
    logger.info(f"Plot resale: {plot_id} from {seller_address} to {current_user.wallet_address} for {price} TON")
    
    return {
        "transaction_id": tx.id,
        "plot_id": plot_id,
        "amount_ton": price,
        "commission": commission,
        "seller_receives": seller_amount,
        "business_transferred": bool(plot.get("business_id"))
    }

# ==================== BUSINESS ROUTES ====================

@api_router.get("/businesses/types")
async def get_business_types(lang: str = "ru"):
    """Get all available business types from the new system"""
    result = {}
    for key, bt in BUSINESSES.items():
        # Get localized name
        name = bt.get("name", {})
        if isinstance(name, dict):
            name_str = name.get(lang) or name.get("ru") or name.get("en") or key
        else:
            name_str = str(name)
        
        result[key] = {
            "name": name_str,
            "tier": bt.get("tier", 1),
            "icon": bt.get("icon", "🏢"),
            "produces": bt.get("produces"),
            "consumes": bt.get("consumes", []),
            "base_production": bt.get("base_production", 0),
            "base_income": bt.get("base_income", 0),
            "base_cost_ton": bt.get("base_cost_ton", 10),
            "daily_wear": bt.get("daily_wear", 0.03),
            "description": bt.get("description", {}).get(lang) or bt.get("description", {}).get("ru") or "",
            "is_patron": bt.get("is_patron", False),
            "patron_type": bt.get("patron_type"),
        }
    return {"business_types": result}

@api_router.get("/businesses")
async def get_all_businesses():
    """Get all businesses"""
    businesses = await db.businesses.find({}, {"_id": 0}).to_list(10000)
    
    result = []
    for b in businesses:
        plot = await db.plots.find_one({"id": b["plot_id"]}, {"_id": 0})
        bt = BUSINESS_TYPES.get(b["business_type"], {})
        income = calculate_business_income(
            b["business_type"], 
            b.get("level", 1), 
            plot.get("zone", "outskirts") if plot else "outskirts",
            len(b.get("connected_businesses", []))
        )
        result.append({
            "id": b["id"],
            "plot_id": b["plot_id"],
            "owner": b["owner"],
            "business_type": b["business_type"],
            "business_name": bt.get("name", {}).get("en", "Unknown"),
            "business_icon": bt.get("icon", "❓"),
            "level": b.get("level", 1),
            "xp": b.get("xp", 0),
            "income": income,
            "storage": b.get("storage", {}),
            "connected_businesses": b.get("connected_businesses", []),
            "is_active": b.get("is_active", True),
            "building_progress": b.get("building_progress", 100),
            "x": plot["x"] if plot else 0,
            "y": plot["y"] if plot else 0,
            "zone": plot.get("zone", "outskirts") if plot else "outskirts"
        })
    
    return {"businesses": result}

@api_router.post("/businesses/build")
async def build_business(request: BuildBusinessRequest, current_user: User = Depends(get_current_user)):
    """Build business using internal balance"""
    lang = current_user.language
    
    plot = await db.plots.find_one({"id": request.plot_id}, {"_id": 0})
    if not plot or plot.get("owner") != current_user.wallet_address:
        raise HTTPException(status_code=404, detail="Plot not found or not owned")
    
    if plot.get("business_id"):
        raise HTTPException(status_code=400, detail="Plot already has a business")
    
    if request.business_type not in BUSINESS_TYPES:
        raise HTTPException(status_code=400, detail="Неверный тип бизнеса")
    
    bt = BUSINESS_TYPES[request.business_type]
    zone = plot.get("zone", "outskirts")
    
    # Check zone restrictions
    if zone not in bt.get("allowed_zones", []):
        raise HTTPException(status_code=400, detail=t("invalid_zone", lang))
    
    # Check per-player limits
    user_biz_count = await db.businesses.count_documents({
        "owner": current_user.wallet_address,
        "business_type": request.business_type
    })
    if user_biz_count >= bt.get("max_per_player", 999):
        raise HTTPException(status_code=400, detail="Maximum businesses of this type reached")
    
    # Check global limits
    if "max_total" in bt:
        total_count = await db.businesses.count_documents({"business_type": request.business_type})
        if total_count >= bt["max_total"]:
            raise HTTPException(status_code=400, detail="Maximum total businesses of this type reached")
    
    # Calculate costs
    materials_cost = bt["materials_required"] * RESOURCE_PRICES.get("materials", 0.005)
    total_cost = bt["cost"] + materials_cost
    
    # Check balance
    if current_user.balance_ton < total_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Need {total_cost} TON, have {current_user.balance_ton} TON"
        )
    
    # Deduct from internal balance
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$inc": {"balance_ton": -total_cost}}
    )
    
    # Create business
    business = Business(
        plot_id=request.plot_id,
        owner=current_user.wallet_address,
        business_type=request.business_type,
        level=1,
        building_progress=100,  # Instant build for now
        is_active=True,
        last_collection=datetime.now(timezone.utc).isoformat()
    )
    business_dict = business.model_dump()
    business_dict['created_at'] = business_dict['created_at'].isoformat()
    business_dict['last_collection'] = business_dict['last_collection']
    await db.businesses.insert_one(business_dict.copy())
    
    # Update plot
    await db.plots.update_one(
        {"id": request.plot_id},
        {"$set": {"business_id": business.id}}
    )
    
    # Update user
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$push": {"businesses_owned": business.id}}
    )
    
    # Record transaction
    tx = Transaction(
        tx_type="build_business",
        from_address=current_user.wallet_address,
        to_address="construction_pool",
        amount_ton=total_cost,
        plot_id=request.plot_id,
        status="completed"
    )
    tx_dict = tx.model_dump()
    tx_dict['created_at'] = tx_dict['created_at'].isoformat()
    await db.transactions.insert_one(tx_dict.copy())
    
    # Record admin income
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {
            "$inc": {
                "building_sales_income": total_cost,
                "total_buildings_sold": 1
            }
        },
        upsert=True
    )
    
    logger.info(f"Business {request.business_type} built by {current_user.wallet_address} for {total_cost} TON")
    
    return {
        "success": True,
        "business_id": business.id,
        "business_type": request.business_type,
        "amount_paid": total_cost,
        "new_balance": current_user.balance_ton - total_cost,
        "message": f"{bt['name']['en']} built successfully!"
    }

@api_router.post("/businesses/confirm-build")
async def confirm_business_build(request: ConfirmTransactionRequest, current_user: User = Depends(get_current_user)):
    """Confirm business building after payment"""
    tx = await db.transactions.find_one({"id": request.transaction_id}, {"_id": 0})
    
    if not tx or tx["from_address"] != current_user.wallet_address:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    
    if tx["status"] == "completed":
        raise HTTPException(status_code=400, detail="Транзакция уже завершена")
    
    plot = await db.plots.find_one({"id": tx["plot_id"]}, {"_id": 0})
    build_order = await db.build_orders.find_one({"plot_id": tx["plot_id"], "owner": current_user.wallet_address, "status": "pending"}, {"_id": 0})
    
    if not build_order:
        raise HTTPException(status_code=404, detail="Build order not found")
    
    bt = BUSINESS_TYPES.get(build_order["business_type"])
    zone = plot.get("zone", "outskirts") if plot else "outskirts"
    
    # Create business (starts building)
    business = Business(
        plot_id=tx["plot_id"],
        owner=current_user.wallet_address,
        business_type=build_order["business_type"],
        income_rate=bt["base_income"],
        production_rate=bt.get("production_rate", 0),
        building_progress=0  # Will be updated by construction companies or time
    )
    business_dict = business.model_dump()
    business_dict['created_at'] = business_dict['created_at'].isoformat()
    business_dict['last_collection'] = business_dict['last_collection'].isoformat()
    await db.businesses.insert_one(business_dict.copy())
    
    # Update plot
    await db.plots.update_one(
        {"id": tx["plot_id"]},
        {"$set": {"business_id": business.id}}
    )
    
    # Update transaction
    await db.transactions.update_one(
        {"id": request.transaction_id},
        {"$set": {"status": "completed", "business_id": business.id, "blockchain_hash": request.blockchain_hash,
                  "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update build order
    await db.build_orders.update_one(
        {"id": build_order["id"]},
        {"$set": {"status": "in_progress", "started_at": datetime.now(timezone.utc).isoformat(),
                  "estimated_completion": (datetime.now(timezone.utc) + timedelta(hours=bt["build_time_hours"])).isoformat()}}
    )
    
    # Update user
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$push": {"businesses_owned": business.id},
         "$inc": {"total_turnover": tx["amount_ton"]}}
    )
    
    # Find and connect related businesses
    await connect_businesses(business.id, build_order["business_type"], plot["x"], plot["y"])
    
    # Broadcast update
    await manager.broadcast({"type": "business_built", "business_id": business.id, "plot_id": tx["plot_id"]})
    
    return {
        "status": "building",
        "business_id": business.id,
        "business_type": build_order["business_type"],
        "build_time_hours": bt["build_time_hours"],
        "message": t("business_built", current_user.language)
    }


@api_router.post("/businesses/demolish/{business_id}")
async def demolish_business(business_id: str, current_user: User = Depends(get_current_user)):
    """Demolish business for 5% of its cost"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    if business["owner"] != current_user.wallet_address:
        raise HTTPException(status_code=403, detail="Not your business")
    
    # Calculate demolish cost (5% of total investment)
    business_config = BUSINESS_TYPES.get(business["business_type"], {})
    base_cost = business_config.get("cost", 0)
    level = business.get("level", 1)
    
    # Calculate total investment
    total_investment = base_cost
    for lvl in range(2, level + 1):
        upgrade_cost = LEVEL_CONFIG.get(lvl, {}).get("upgrade_cost", 0)
        total_investment += upgrade_cost
    
    demolish_cost = total_investment * DEMOLISH_COST  # 5%
    
    # Check balance
    user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if user["balance_ton"] < demolish_cost:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Need {demolish_cost} TON for demolition")
    
    # Deduct demolish cost
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$inc": {"balance_ton": -demolish_cost}}
    )
    
    # Remove business from plot
    plot = await db.plots.find_one({"business_id": business_id}, {"_id": 0})
    if plot:
        await db.plots.update_one(
            {"id": plot["id"]},
            {"$set": {"business_id": None}}
        )
    
    # Delete business
    await db.businesses.delete_one({"id": business_id})
    
    # Remove from user's businesses list
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$pull": {"businesses_owned": business_id}}
    )
    
    # Add to treasury
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"demolish_fees": demolish_cost, "total_income": demolish_cost}},
        upsert=True
    )
    
    # Record transaction
    tx = Transaction(
        tx_type="demolish_business",
        from_address=current_user.wallet_address,
        to_address="treasury",
        amount_ton=demolish_cost,
        commission=0,
        metadata={"business_id": business_id, "business_type": business["business_type"], "level": level}
    )
    tx_dict = tx.model_dump()
    tx_dict['created_at'] = tx_dict['created_at'].isoformat()
    await db.transactions.insert_one(tx_dict)
    
    logger.info(f"Business demolished: {business_id} by {current_user.wallet_address} for {demolish_cost} TON")
    
    return {
        "status": "demolished",
        "business_id": business_id,
        "demolish_cost": demolish_cost,
        "plot_freed": bool(plot)
    }

async def connect_businesses(business_id: str, business_type: str, x: int, y: int):
    """Connect business with nearby compatible businesses"""
    bt = BUSINESS_TYPES.get(business_type, {})
    requires = bt.get("requires")
    produces = bt.get("produces")
    
    # Find nearby businesses (within 5 tiles)
    nearby_plots = await db.plots.find({
        "business_id": {"$exists": True, "$ne": None},
        "x": {"$gte": x - 5, "$lte": x + 5},
        "y": {"$gte": y - 5, "$lte": y + 5}
    }, {"_id": 0}).to_list(100)
    
    connections = []
    for plot in nearby_plots:
        if plot.get("business_id") == business_id:
            continue
        
        nearby_business = await db.businesses.find_one({"id": plot["business_id"]}, {"_id": 0})
        if not nearby_business:
            continue
        
        nearby_bt = BUSINESS_TYPES.get(nearby_business["business_type"], {})
        
        if requires and nearby_bt.get("produces") == requires:
            connections.append(nearby_business["id"])
            await db.businesses.update_one(
                {"id": nearby_business["id"]},
                {"$addToSet": {"connected_businesses": business_id}}
            )
        
        if produces and nearby_bt.get("requires") == produces:
            connections.append(nearby_business["id"])
            await db.businesses.update_one(
                {"id": nearby_business["id"]},
                {"$addToSet": {"connected_businesses": business_id}}
            )
    
    if connections:
        await db.businesses.update_one(
            {"id": business_id},
            {"$set": {"connected_businesses": connections}}
        )

@api_router.post("/businesses/collect/{business_id}")
async def collect_income(business_id: str, current_user: User = Depends(get_current_user)):
    """Collect accumulated income from business"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Check ownership using consistent user ID logic
    user = await db.users.find_one({"$or": [
        {"wallet_address": current_user.wallet_address},
        {"email": current_user.email},
        {"username": current_user.username}
    ]})
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_id = user.get("id", str(user.get("_id")))
    
    if business["owner"] != user_id and business["owner"] != current_user.wallet_address:
        raise HTTPException(status_code=404, detail="Business not found")
    
    if business.get("building_progress", 100) < 100:
        raise HTTPException(status_code=400, detail="Business still under construction")
    
    plot = await db.plots.find_one({"id": business["plot_id"]}, {"_id": 0})
    zone = plot.get("zone", "outskirts") if plot else "outskirts"
    
    # Calculate income since last collection
    last_collection = datetime.fromisoformat(business["last_collection"]) if isinstance(business["last_collection"], str) else business["last_collection"]
    hours_passed = (datetime.now(timezone.utc) - last_collection).total_seconds() / 3600
    days_passed = hours_passed / 24
    
    income_data = calculate_business_income(
        business["business_type"],
        business.get("level", 1),
        zone,
        len(business.get("connected_businesses", []))
    )
    
    gross_income = income_data["gross"] * days_passed
    tax = gross_income * BASE_TAX_RATE
    net_income = gross_income - tax
    
    # Update business
    await db.businesses.update_one(
        {"id": business_id},
        {"$set": {"last_collection": datetime.now(timezone.utc).isoformat()},
         "$inc": {"xp": int(gross_income * 10)}}
    )
    
    # Update user balance
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$inc": {"balance_ton": net_income, "total_income": net_income}}
    )
    
    # Record tax
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"total_tax": tax}},
        upsert=True
    )
    
    # Check level up
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    new_level = 1
    for level, config in sorted(LEVEL_CONFIG.items(), reverse=True):
        if business.get("xp", 0) >= config["xp_required"]:
            new_level = level
            break
    
    if new_level > business.get("level", 1):
        await db.businesses.update_one({"id": business_id}, {"$set": {"level": new_level}})
    
    return {
        "collected": round(net_income, 4),
        "gross": round(gross_income, 4),
        "tax": round(tax, 4),
        "hours_passed": round(hours_passed, 2),
        "new_xp": business.get("xp", 0),
        "level": new_level
    }

# ==================== TRADE ROUTES ====================

@api_router.post("/trade/contract")
async def create_contract(request: CreateContractRequest, current_user: User = Depends(get_current_user)):
    """Create a resource supply contract"""
    seller_biz = await db.businesses.find_one({"id": request.seller_business_id}, {"_id": 0})
    buyer_biz = await db.businesses.find_one({"id": request.buyer_business_id}, {"_id": 0})
    
    if not seller_biz or seller_biz["owner"] != current_user.wallet_address:
        raise HTTPException(status_code=404, detail="Seller business not found")
    
    if not buyer_biz:
        raise HTTPException(status_code=404, detail="Buyer business not found")
    
    seller_bt = BUSINESS_TYPES.get(seller_biz["business_type"], {})
    buyer_bt = BUSINESS_TYPES.get(buyer_biz["business_type"], {})
    
    if seller_bt.get("produces") != request.resource_type:
        raise HTTPException(status_code=400, detail="Seller doesn't produce this resource")
    
    if buyer_bt.get("requires") != request.resource_type:
        raise HTTPException(status_code=400, detail="Buyer doesn't need this resource")
    
    contract = Contract(
        seller_id=current_user.wallet_address,
        buyer_id=buyer_biz["owner"],
        seller_business_id=request.seller_business_id,
        buyer_business_id=request.buyer_business_id,
        resource_type=request.resource_type,
        amount_per_hour=request.amount_per_hour,
        price_per_unit=request.price_per_unit,
        expires_at=(datetime.now(timezone.utc) + timedelta(days=request.duration_days)).isoformat()
    )
    contract_dict = contract.model_dump()
    contract_dict['created_at'] = contract_dict['created_at'].isoformat()
    await db.contracts.insert_one(contract_dict.copy())
    
    return {"contract_id": contract.id, "status": "pending_acceptance"}

@api_router.post("/trade/contract/accept/{contract_id}")
async def accept_contract(contract_id: str, current_user: User = Depends(get_current_user)):
    """Accept a supply contract"""
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    
    if not contract or contract["buyer_id"] != current_user.wallet_address:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    await db.contracts.update_one(
        {"id": contract_id},
        {"$set": {"is_active": True}}
    )
    
    return {"status": "accepted", "contract_id": contract_id}

@api_router.post("/trade/spot")
async def spot_trade(request: TradeResourceRequest, current_user: User = Depends(get_current_user)):
    """Execute spot trade between businesses"""
    seller_biz = await db.businesses.find_one({"id": request.seller_business_id}, {"_id": 0})
    buyer_biz = await db.businesses.find_one({"id": request.buyer_business_id}, {"_id": 0})
    
    if not seller_biz or not buyer_biz:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Verify ownership
    if seller_biz["owner"] != current_user.wallet_address and buyer_biz["owner"] != current_user.wallet_address:
        raise HTTPException(status_code=403, detail="Not your business")
    
    # Get current market price
    base_price = RESOURCE_PRICES.get(request.resource_type, 0.01)
    total_value = request.amount * base_price
    commission = total_value * TRADE_COMMISSION  # Now 0%
    
    # Apply income tax to seller's earnings (13% base rate)
    income_tax = total_value * BASE_TAX_RATE
    seller_receives = total_value - income_tax
    
    # Update seller balance
    await db.users.update_one(
        {"wallet_address": seller_biz["owner"]},
        {"$inc": {"balance_ton": seller_receives, "total_income": seller_receives}}
    )
    
    # Update buyer balance (full payment)
    await db.users.update_one(
        {"wallet_address": buyer_biz["owner"]},
        {"$inc": {"balance_ton": -total_value}}
    )
    
    # Record tax to treasury
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"total_tax": income_tax}},
        upsert=True
    )
    
    tx = Transaction(
        tx_type="trade_resource",
        from_address=buyer_biz["owner"],
        to_address=seller_biz["owner"],
        amount_ton=total_value,
        commission=income_tax,  # Now this is income tax, not trade commission
        resource_type=request.resource_type,
        resource_amount=request.amount
    )
    tx_dict = tx.model_dump()
    tx_dict['created_at'] = tx_dict['created_at'].isoformat()
    await db.transactions.insert_one(tx_dict.copy())
    
    return {
        "transaction_id": tx.id,
        "resource": request.resource_type,
        "amount": request.amount,
        "total_value": total_value,
        "income_tax": income_tax,
        "seller_receives": seller_receives
    }

@api_router.get("/trade/contracts")
async def get_user_contracts(current_user: User = Depends(get_current_user)):
    """Get user's contracts"""
    contracts = await db.contracts.find({
        "$or": [
            {"seller_id": current_user.wallet_address},
            {"buyer_id": current_user.wallet_address}
        ]
    }, {"_id": 0}).to_list(100)
    
    return {"contracts": contracts}

# ==================== MARKETPLACE ====================

class MarketListing(BaseModel):
    resource_type: str
    amount: float
    price_per_unit: float  # Цена устанавливается продавцом
    business_id: str

class BuyFromMarketRequest(BaseModel):
    listing_id: str
    amount: float

@api_router.post("/market/list")
async def create_market_listing(data: MarketListing, current_user: User = Depends(get_current_user)):
    """Выставить ресурсы на продажу с собственной ценой"""
    # Проверяем что бизнес принадлежит пользователю
    business = await db.businesses.find_one({"id": data.business_id}, {"_id": 0})
    
    # Get user from database
    user = None
    if current_user.wallet_address:
        user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if not user and current_user.email:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_id = user.get("id", str(user.get("_id")))
    
    # Check business ownership by user_id or wallet
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    if business["owner"] != user_id and business["owner"] != current_user.wallet_address:
        raise HTTPException(status_code=403, detail="Not your business")
    
    # Use BUSINESSES config from business_config.py (not BUSINESS_TYPES)
    bt = BUSINESSES.get(business["business_type"], {})
    business_produces = bt.get("produces")
    
    # If not in BUSINESSES, check BUSINESS_TYPES as fallback
    if not bt:
        bt = BUSINESS_TYPES.get(business["business_type"], {})
        business_produces = bt.get("produces")
    
    if business_produces != data.resource_type:
        raise HTTPException(status_code=400, detail=f"This business doesn't produce {data.resource_type}. It produces: {business_produces}")
    
    # Проверяем минимальную цену (не ниже 50% от базовой)
    base_price = RESOURCE_PRICES.get(data.resource_type, 0.01)
    min_price = base_price * 0.5
    if data.price_per_unit < min_price:
        raise HTTPException(status_code=400, detail=f"Price too low. Minimum: {min_price} TON")
    
    listing = {
        "id": str(uuid.uuid4()),
        "seller_id": user_id,  # Use user_id instead of wallet_address
        "seller_email": user.get("email"),
        "seller_username": user.get("username") or current_user.display_name,
        "business_id": data.business_id,
        "resource_type": data.resource_type,
        "amount": data.amount,
        "price_per_unit": data.price_per_unit,
        "total_price": data.amount * data.price_per_unit,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.market_listings.insert_one(listing.copy())
    
    logger.info(f"Market listing created: {data.amount} {data.resource_type} @ {data.price_per_unit} TON by {user.get('username')}")
    
    return {"status": "listed", "listing": listing}

@api_router.get("/market/listings")
async def get_market_listings(resource_type: str = None, sort_by: str = "price"):
    """Получить все активные предложения на рынке"""
    query = {"status": "active"}
    if resource_type:
        query["resource_type"] = resource_type
    
    sort_field = "price_per_unit" if sort_by == "price" else "created_at"
    sort_order = 1 if sort_by == "price" else -1
    
    listings = await db.market_listings.find(query, {"_id": 0}).sort(sort_field, sort_order).to_list(100)
    
    return {"listings": listings, "total": len(listings)}

@api_router.post("/market/buy")
async def buy_from_market(data: BuyFromMarketRequest, current_user: User = Depends(get_current_user)):
    """Купить ресурсы с рынка"""
    listing = await db.market_listings.find_one({"id": data.listing_id, "status": "active"}, {"_id": 0})
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or no longer active")
    
    # Get buyer from database
    buyer = None
    if current_user.wallet_address:
        buyer = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if not buyer and current_user.email:
        buyer = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    
    buyer_id = buyer.get("id", str(buyer.get("_id")))
    
    # Check not buying own listing
    if listing["seller_id"] == buyer_id or listing.get("seller_email") == buyer.get("email"):
        raise HTTPException(status_code=400, detail="Cannot buy your own listing")
    
    if data.amount > listing["amount"]:
        raise HTTPException(status_code=400, detail=f"Not enough resources. Available: {listing['amount']}")
    
    # Рассчитываем стоимость
    total_cost = data.amount * listing["price_per_unit"]
    
    # Проверяем баланс покупателя
    if buyer.get("balance_ton", 0) < total_cost:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Need {total_cost} TON")
    
    # Налог с продавца (13%)
    seller_tax = total_cost * BASE_TAX_RATE
    seller_receives = total_cost - seller_tax
    
    # Find seller for balance update
    seller_filter = {"id": listing["seller_id"]}
    if listing.get("seller_email"):
        seller_filter = {"email": listing["seller_email"]}
    
    # Обновляем баланс покупателя
    buyer_filter = {"email": buyer.get("email")} if buyer.get("email") else {"id": buyer_id}
    await db.users.update_one(
        buyer_filter,
        {"$inc": {"balance_ton": -total_cost}}
    )
    
    # Обновляем баланс продавца
    await db.users.update_one(
        seller_filter,
        {"$inc": {"balance_ton": seller_receives, "total_income": seller_receives}}
    )
    
    # Обновляем листинг
    new_amount = listing["amount"] - data.amount
    if new_amount <= 0:
        await db.market_listings.update_one(
            {"id": data.listing_id},
            {"$set": {"status": "sold", "sold_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        await db.market_listings.update_one(
            {"id": data.listing_id},
            {"$set": {"amount": new_amount, "total_price": new_amount * listing["price_per_unit"]}}
        )
    
    # Налог в казну
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"market_tax": seller_tax, "total_tax": seller_tax}},
        upsert=True
    )
    
    # Записываем транзакцию
    tx = {
        "id": str(uuid.uuid4()),
        "tx_type": "market_purchase",
        "from_address": current_user.wallet_address,
        "to_address": listing["seller_id"],
        "amount_ton": total_cost,
        "tax": seller_tax,
        "resource_type": listing["resource_type"],
        "resource_amount": data.amount,
        "listing_id": data.listing_id,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.transactions.insert_one(tx)
    
    logger.info(f"Market purchase: {data.amount} {listing['resource_type']} for {total_cost} TON")
    
    return {
        "status": "purchased",
        "amount": data.amount,
        "resource_type": listing["resource_type"],
        "total_paid": total_cost,
        "seller_received": seller_receives,
        "tax": seller_tax
    }

@api_router.delete("/market/listing/{listing_id}")
async def cancel_market_listing(listing_id: str, current_user: User = Depends(get_current_user)):
    """Отменить свой листинг"""
    listing = await db.market_listings.find_one({"id": listing_id}, {"_id": 0})
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing["seller_id"] != current_user.wallet_address:
        raise HTTPException(status_code=403, detail="Not your listing")
    
    await db.market_listings.update_one(
        {"id": listing_id},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "cancelled", "listing_id": listing_id}

@api_router.get("/market/my-listings")
async def get_my_listings(current_user: User = Depends(get_current_user)):
    """Получить свои листинги"""
    # Search by user_id or email
    user = None
    if current_user.wallet_address:
        user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if not user and current_user.email:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    
    if not user:
        return {"listings": []}
    
    user_id = user.get("id", str(user.get("_id")))
    
    listings = await db.market_listings.find(
        {"$or": [{"seller_id": user_id}, {"seller_id": current_user.wallet_address}, {"seller_email": user.get("email")}], "status": "active"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {"listings": listings}


@api_router.get("/my/resources")
async def get_my_resources(current_user: User = Depends(get_current_user)):
    """Получить ресурсы пользователя"""
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        return {"resources": {}}
    
    user = ui["user"]
    
    # Get resources directly from user document
    user_resources = user.get("resources", {})
    
    # Also aggregate from business storages as backup
    user_id = user.get("id")
    user_ids = ui["ids"]
    
    businesses = await db.businesses.find(
        {"$or": [{"owner": uid} for uid in user_ids]},
        {"_id": 0, "storage": 1}
    ).to_list(100)
    
    for biz in businesses:
        storage = biz.get("storage", {})
        items = storage.get("items", {})
        for resource, amount in items.items():
            if amount > 0:
                user_resources[resource] = user_resources.get(resource, 0) + int(amount)
    
    # Filter out zero and negative values
    resources = {k: round(v, 2) for k, v in user_resources.items() if v > 0}
    
    return {"resources": resources}


# ==================== TRADE OPERATIONS (COOPERATION) ====================

@api_router.get("/my/trade-operations")
async def get_my_trade_operations(current_user: User = Depends(get_current_user)):
    """Get user's trade operations history + shared warehouse info"""
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        return {"operations": {"bought": {}, "sold": {}}, "warehouse": {"capacity": 0, "used": 0, "items": {}}}
    
    user = ui["user"]
    user_id = user.get("id", str(user.get("_id")))
    
    # Get all businesses to calculate shared warehouse
    businesses = await db.businesses.find(
        get_businesses_query(ui["ids"]),
        {"_id": 0}
    ).to_list(100)
    
    # Calculate shared warehouse
    total_capacity = 0
    total_used = 0
    all_items = {}
    
    for biz in businesses:
        storage = biz.get("storage", {})
        capacity = storage.get("capacity", 0)
        total_capacity += capacity
        items = storage.get("items", {})
        for resource, amount in items.items():
            if amount > 0:
                all_items[resource] = all_items.get(resource, 0) + int(amount)
                total_used += int(amount)
    
    # Get purchase/sale transactions
    user_ids_list = list(ui["ids"])
    
    bought = {}
    sold = {}
    
    # Purchases (buyer)
    buy_txs = await db.transactions.find(
        {"tx_type": "market_purchase", "$or": [{"from_address": {"$in": user_ids_list}}, {"buyer_id": {"$in": user_ids_list}}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    
    for tx in buy_txs:
        rt = tx.get("resource_type", "unknown")
        bought[rt] = bought.get(rt, 0) + int(tx.get("resource_amount", 0))
    
    # Sales (seller)
    sell_txs = await db.transactions.find(
        {"tx_type": "market_purchase", "$or": [{"to_address": {"$in": user_ids_list}}, {"seller_id": {"$in": user_ids_list}}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    
    for tx in sell_txs:
        rt = tx.get("resource_type", "unknown")
        sold[rt] = sold.get(rt, 0) + int(tx.get("resource_amount", 0))
    
    # Also count from market listings
    sold_listings = await db.market_listings.find(
        {"seller_id": {"$in": user_ids_list}, "status": "sold"},
        {"_id": 0}
    ).to_list(200)
    
    for listing in sold_listings:
        rt = listing.get("resource_type", "unknown")
        # Only count if not already counted in transactions
        if rt not in sold:
            sold[rt] = 0
    
    # Calculate overflow
    overflow = max(0, total_used - total_capacity)
    spoilage_per_day = int(overflow * 0.5) if overflow > 0 else 0
    
    return {
        "operations": {
            "bought": bought,
            "sold": sold,
        },
        "warehouse": {
            "capacity": total_capacity,
            "used": total_used,
            "items": all_items,
            "overflow": overflow,
            "spoilage_per_day": spoilage_per_day,
            "is_overflowing": overflow > 0,
        }
    }


class ResourceListingRequest(BaseModel):
    resource_type: str
    amount: int  # Must be integer
    price_per_unit: float


@api_router.post("/market/list-resource")
async def list_resource_for_sale(data: ResourceListingRequest, current_user: User = Depends(get_current_user)):
    """Выставить ресурсы на продажу (из складов бизнесов)"""
    # Validate integer amount
    amount = int(data.amount)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Количество должно быть больше 0")
    
    # Validate price (max 2 decimals)
    price = round(data.price_per_unit, 2)
    if price < 0.01:
        raise HTTPException(status_code=400, detail="Минимальная цена: 0.01 TON")
    
    # Get user
    user = None
    if current_user.wallet_address:
        user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if not user and current_user.email:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_id = user.get("id", str(user.get("_id")))
    
    # Get businesses with this resource
    businesses = await db.businesses.find(
        {"$or": [{"owner": user_id}, {"owner": current_user.wallet_address}]},
        {"_id": 0}
    ).to_list(100)
    
    # Find available amount
    total_available = 0
    source_businesses = []
    
    for biz in businesses:
        storage = biz.get("storage", {})
        items = storage.get("items", {})
        biz_amount = int(items.get(data.resource_type, 0))
        if biz_amount > 0:
            total_available += biz_amount
            source_businesses.append({"id": biz["id"], "amount": biz_amount})
    
    if total_available < amount:
        raise HTTPException(status_code=400, detail=f"Недостаточно ресурсов. Доступно: {total_available}")
    
    # Deduct resources from businesses
    remaining = amount
    for source in source_businesses:
        if remaining <= 0:
            break
        
        take_amount = min(source["amount"], remaining)
        remaining -= take_amount
        
        # Update business storage
        await db.businesses.update_one(
            {"id": source["id"]},
            {"$inc": {f"storage.items.{data.resource_type}": -take_amount}}
        )
    
    # Create listing
    listing = {
        "id": str(uuid.uuid4()),
        "seller_id": user_id,
        "seller_email": user.get("email"),
        "seller_username": user.get("username") or current_user.display_name,
        "business_id": None,  # Sold from user storage
        "resource_type": data.resource_type,
        "amount": amount,
        "price_per_unit": price,
        "total_price": round(amount * price, 2),
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.market_listings.insert_one(listing.copy())
    
    logger.info(f"Resource listing created: {amount} {data.resource_type} @ {price} TON by {user.get('username')}")
    
    return {"status": "listed", "listing": listing}


@api_router.post("/market/cancel/{listing_id}")
async def cancel_listing(listing_id: str, current_user: User = Depends(get_current_user)):
    """Отменить листинг и вернуть ресурсы"""
    listing = await db.market_listings.find_one({"id": listing_id, "status": "active"}, {"_id": 0})
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Get user
    user = None
    if current_user.wallet_address:
        user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if not user and current_user.email:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_id = user.get("id", str(user.get("_id")))
    
    # Check ownership
    if listing["seller_id"] != user_id and listing.get("seller_email") != user.get("email"):
        raise HTTPException(status_code=403, detail="Not your listing")
    
    # Return resources to first business (simplified)
    first_business = await db.businesses.find_one(
        {"$or": [{"owner": user_id}, {"owner": current_user.wallet_address}]},
        {"_id": 0}
    )
    
    if first_business:
        await db.businesses.update_one(
            {"id": first_business["id"]},
            {"$inc": {f"storage.items.{listing['resource_type']}": listing["amount"]}}
        )
    
    # Mark as cancelled
    await db.market_listings.update_one(
        {"id": listing_id},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "cancelled"}


# ==================== LAND MARKETPLACE ====================

class LandListingRequest(BaseModel):
    plot_id: str
    price: float  # Цена устанавливается продавцом

class BuyLandRequest(BaseModel):
    listing_id: str

@api_router.post("/market/land/list")
async def create_land_listing(data: LandListingRequest, current_user: User = Depends(get_current_user)):
    """Выставить участок земли на продажу"""
    # Получаем участок
    plot = await db.plots.find_one({"id": data.plot_id}, {"_id": 0})
    
    if not plot:
        raise HTTPException(status_code=404, detail="Участок не найден")
    
    # Проверяем владельца (по user.id)
    user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    user_id = user.get("id", str(user.get("_id")))
    
    if plot.get("owner") != user_id and plot.get("owner") != current_user.wallet_address:
        raise HTTPException(status_code=403, detail="You don't own this plot")
    
    # Проверяем что участок не уже на продаже
    existing = await db.land_listings.find_one({"plot_id": data.plot_id, "status": "active"})
    if existing:
        raise HTTPException(status_code=400, detail="Этот участок уже выставлен на продажу. Сначала отмените текущий листинг.")
    
    # Минимальная цена - 50% от изначальной
    min_price = plot.get("price", 0.1) * 0.5
    if data.price < min_price:
        raise HTTPException(status_code=400, detail=f"Price too low. Minimum: {min_price:.4f} TON")
    
    # Получаем информацию о городе/острова
    city_id = plot.get("city_id") or plot.get("island_id") or "ton_island"
    city = await db.cities.find_one({"id": city_id}, {"_id": 0, "name": 1})
    
    # Handle localized name - default to TON Island for island plots
    city_name = "TON Island"
    if city:
        name = city.get("name")
        if isinstance(name, dict):
            city_name = name.get("ru") or name.get("en") or "TON Island"
        elif isinstance(name, str):
            city_name = name
    elif city_id == "ton_island":
        city_name = "TON Island"
    
    # Получаем бизнес на участке (если есть)
    plot_city_id = plot.get("city_id") or plot.get("island_id") or "ton_island"
    business = await db.businesses.find_one({
        "$or": [
            {"city_id": plot_city_id, "plot_x": plot.get("x"), "plot_y": plot.get("y")},
            {"island_id": plot_city_id, "plot_x": plot.get("x"), "plot_y": plot.get("y")}
        ]
    }, {"_id": 0})
    
    business_info = None
    if business:
        # Считаем связи
        connections_count = len(business.get("connected_businesses", []))
        business_info = {
            "type": business.get("business_type"),
            "level": business.get("level", 1),
            "connections": connections_count,
            "xp": business.get("xp", 0)
        }
    
    listing = {
        "id": str(uuid.uuid4()),
        "plot_id": data.plot_id,
        "city_id": plot.get("city_id") or plot.get("island_id") or "ton_island",
        "city_name": city_name,
        "x": plot.get("x"),
        "y": plot.get("y"),
        "seller_id": user.get("id") or current_user.id,
        "seller_wallet": current_user.wallet_address,
        "seller_username": user.get("username") or user.get("display_name", "Anonymous"),
        "original_price": plot.get("price", 0),
        "price": data.price,
        "business": business_info,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.land_listings.insert_one(listing.copy())
    
    # Mark plot as on_sale
    await db.plots.update_one(
        {"id": data.plot_id},
        {"$set": {"on_sale": True, "listing_id": listing["id"]}}
    )
    
    # If there's a business, mark it as on_sale too
    if business:
        await db.businesses.update_one(
            {"id": business.get("id")},
            {"$set": {"on_sale": True, "listing_id": listing["id"], "status": "on_sale"}}
        )
    
    logger.info(f"Land listing created: plot {data.plot_id} @ {data.price} TON by {current_user.username}")
    
    return {"status": "listed", "listing": listing}

@api_router.get("/market/land/listings")
async def get_land_listings(city_id: str = None, sort_by: str = "price", has_business: bool = None):
    """Получить все активные предложения земли"""
    query = {"status": "active"}
    
    if city_id:
        query["city_id"] = city_id
    
    if has_business is not None:
        if has_business:
            query["business"] = {"$ne": None}
        else:
            query["business"] = None
    
    sort_field = "price" if sort_by == "price" else "created_at"
    sort_order = 1 if sort_by == "price" else -1
    
    listings = await db.land_listings.find(query, {"_id": 0}).sort(sort_field, sort_order).to_list(100)
    
    return {"listings": listings, "total": len(listings)}

@api_router.post("/market/land/buy")
async def buy_land_from_market(data: BuyLandRequest, current_user: User = Depends(get_current_user)):
    """Купить участок земли с маркетплейса"""
    listing = await db.land_listings.find_one({"id": data.listing_id, "status": "active"}, {"_id": 0})
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or no longer active")
    
    # Check if buyer is trying to buy their own listing (compare by user ID)
    buyer = await db.users.find_one({"$or": [
        {"wallet_address": current_user.wallet_address} if current_user.wallet_address else {"_id": None},
        {"id": current_user.id}
    ]}, {"_id": 0})
    
    if not buyer:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    buyer_id = buyer.get("id") or current_user.id
    
    # Check both seller_id and seller_user_id (for backward compatibility)
    seller_id = listing.get("seller_id") or listing.get("seller_user_id")
    if seller_id == buyer_id or (current_user.wallet_address and seller_id == current_user.wallet_address):
        raise HTTPException(status_code=400, detail="Нельзя купить свой собственный листинг")
    
    # Проверяем баланс покупателя
    if buyer["balance_ton"] < listing["price"]:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Need {listing['price']} TON")
    
    # Налог с продавца (10%)
    seller_tax = listing["price"] * BASE_TAX_RATE
    seller_receives = listing["price"] - seller_tax
    
    # Обновляем баланс покупателя (по id)
    new_buyer_balance = buyer["balance_ton"] - listing["price"]
    await db.users.update_one(
        {"id": buyer_id},
        {"$inc": {"balance_ton": -listing["price"]}}
    )
    
    # Обновляем баланс продавца (по seller_id или seller_user_id)
    seller_id = listing.get("seller_id") or listing.get("seller_user_id")
    if seller_id:
        await db.users.update_one(
            {"$or": [{"id": seller_id}, {"wallet_address": seller_id}]},
            {"$inc": {"balance_ton": seller_receives, "total_income": seller_receives}}
        )
    
    # Передаём владение участком
    await db.plots.update_one(
        {"id": listing["plot_id"]},
        {"$set": {
            "owner": buyer_id,
            "owner_username": buyer.get("username"),
            "owner_avatar": buyer.get("avatar"),
            "purchased_at": datetime.now(timezone.utc).isoformat(),
            "price": listing["price"]
        },
        "$unset": {"on_sale": "", "listing_id": ""}}
    )
    
    # Если есть бизнес - передаём его тоже
    if listing.get("business"):
        plot_city_id = listing.get("city_id") or listing.get("island_id") or "ton_island"
        await db.businesses.update_one(
            {"$or": [
                {"city_id": plot_city_id, "plot_x": listing.get("x"), "plot_y": listing.get("y")},
                {"island_id": plot_city_id, "plot_x": listing.get("x"), "plot_y": listing.get("y")},
                {"id": listing.get("business_id")}
            ]},
            {"$set": {
                "owner": buyer_id,
                "owner_wallet": current_user.wallet_address,
                "owner_username": buyer.get("username")
            },
            "$unset": {"on_sale": "", "listing_id": ""}}
        )
    
    # Закрываем листинг
    await db.land_listings.update_one(
        {"id": data.listing_id},
        {"$set": {
            "status": "sold",
            "buyer_id": buyer_id,
            "buyer_username": buyer.get("username"),
            "sold_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Налог в казну
    await db.admin_stats.update_one(
        {"type": "treasury"},
        {"$inc": {"land_market_tax": seller_tax, "total_tax": seller_tax}},
        upsert=True
    )
    
    # Получаем city_name как строку (может быть объектом с en/ru)
    city_name_raw = listing.get("city_name", "TON Island")
    if isinstance(city_name_raw, dict):
        city_name_str = city_name_raw.get("ru") or city_name_raw.get("en") or "TON Island"
    else:
        city_name_str = city_name_raw or "TON Island"
    
    # Determine transaction type based on whether it has business
    has_business = listing.get("business") is not None
    tx_type_buyer = "business_purchase" if has_business else "land_purchase"
    tx_type_seller = "business_sale" if has_business else "land_sale"
    
    # Description with business name if applicable
    if has_business:
        business_name = listing.get("business", {}).get("name", "Бизнес")
        description_buyer = f"Покупка бизнеса «{business_name}» на {city_name_str}"
        description_seller = f"Продажа бизнеса «{business_name}» на {city_name_str}"
    else:
        description_buyer = f"Покупка участка [{listing['x']}, {listing['y']}] на {city_name_str}"
        description_seller = f"Продажа участка [{listing['x']}, {listing['y']}] на {city_name_str}"
    
    # Записываем транзакцию покупателя (отрицательная сумма - расход)
    tx = {
        "id": str(uuid.uuid4()),
        "type": tx_type_buyer,
        "user_id": buyer_id,
        "from_user_id": buyer_id,
        "to_user_id": listing["seller_id"],
        "from_address": current_user.wallet_address,
        "to_address": listing.get("seller_wallet"),
        "amount": -listing["price"],  # Negative - buyer spent money
        "amount_ton": listing["price"],
        "tax": seller_tax,
        "plot_id": listing["plot_id"],
        "city_id": listing["city_id"],
        "listing_id": data.listing_id,
        "description": description_buyer,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.transactions.insert_one(tx)
    
    # Also create transaction for seller (положительная сумма - доход)
    seller_tx = {
        "id": str(uuid.uuid4()),
        "type": tx_type_seller,
        "user_id": listing["seller_id"],
        "from_user_id": buyer_id,
        "to_user_id": listing["seller_id"],
        "amount": seller_receives,  # Positive - seller received money
        "amount_ton": seller_receives,
        "tax": seller_tax,
        "plot_id": listing["plot_id"],
        "city_id": listing["city_id"],
        "listing_id": data.listing_id,
        "description": description_seller,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.transactions.insert_one(seller_tx)
    
    logger.info(f"Land purchase: plot {listing['plot_id']} for {listing['price']} TON")
    
    return {
        "status": "purchased",
        "plot_id": listing["plot_id"],
        "city_name": city_name_str,
        "total_paid": listing["price"],
        "seller_received": seller_receives,
        "tax": seller_tax,
        "has_business": listing.get("business") is not None,
        "new_balance": new_buyer_balance
    }

@api_router.delete("/market/land/listing/{listing_id}")
async def cancel_land_listing(listing_id: str, current_user: User = Depends(get_current_user)):
    """Отменить листинг земли"""
    listing = await db.land_listings.find_one({"id": listing_id}, {"_id": 0})
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Получаем пользователя по разным идентификаторам
    user = None
    if current_user.wallet_address:
        user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if not user and current_user.email:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    if not user:
        user = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    
    user_id = user.get("id") if user else current_user.id
    
    # Проверяем владение по всем возможным идентификаторам
    seller_id = listing.get("seller_id")
    seller_wallet = listing.get("seller_wallet")
    seller_user_id = listing.get("seller_user_id")
    
    is_owner = (
        seller_id == user_id or 
        seller_wallet == current_user.wallet_address or
        seller_user_id == user_id or
        seller_id == current_user.wallet_address
    )
    
    if not is_owner:
        raise HTTPException(status_code=403, detail="Not your listing")
    
    await db.land_listings.update_one(
        {"id": listing_id},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Remove on_sale mark from plot
    await db.plots.update_one(
        {"id": listing.get("plot_id")},
        {"$unset": {"on_sale": "", "listing_id": ""}}
    )
    
    # Remove on_sale mark from business if exists
    if listing.get("business"):
        # Try to find business by business_id first
        business_id = listing.get("business_id")
        if business_id:
            await db.businesses.update_one(
                {"id": business_id},
                {"$unset": {"on_sale": "", "listing_id": ""}, "$set": {"status": "working"}}
            )
        else:
            # Fallback to coordinates
            plot_city_id = listing.get("city_id") or "ton_island"
            await db.businesses.update_one(
                {"$or": [
                    {"city_id": plot_city_id, "x": listing.get("x"), "y": listing.get("y")},
                    {"island_id": plot_city_id, "x": listing.get("x"), "y": listing.get("y")}
                ]},
                {"$unset": {"on_sale": "", "listing_id": ""}, "$set": {"status": "working"}}
            )
    
    return {"status": "cancelled", "listing_id": listing_id}

@api_router.get("/market/land/my-listings")
async def get_my_land_listings(current_user: User = Depends(get_current_user)):
    """Получить свои листинги земли"""
    # Находим пользователя по разным идентификаторам
    user = None
    if current_user.wallet_address:
        user = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if not user and current_user.email:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    if not user:
        user = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    
    user_id = user.get("id") if user else current_user.id
    
    # Ищем листинги по всем возможным идентификаторам продавца
    or_conditions = [{"seller_id": user_id}]
    if current_user.wallet_address:
        or_conditions.append({"seller_id": current_user.wallet_address})
        or_conditions.append({"seller_wallet": current_user.wallet_address})
    if user and user.get("id"):
        or_conditions.append({"seller_user_id": user.get("id")})
    
    listings = await db.land_listings.find(
        {"$or": or_conditions},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {"listings": listings}


# ==================== BUSINESS SALE API ====================

class SellBusinessRequest(BaseModel):
    price: float  # Цена устанавливается продавцом

class CalculateSaleTaxRequest(BaseModel):
    price: float

@api_router.post("/business/calculate-sale-tax")
async def calculate_sale_tax(data: CalculateSaleTaxRequest):
    """Рассчитать налог с продажи (показать пользователю перед продажей)"""
    # Получаем налог из настроек админа
    tax_settings = await db.admin_settings.find_one({"type": "tax_settings"}, {"_id": 0})
    tax_rate = (tax_settings.get("land_business_sale_tax", 10) if tax_settings else 10) / 100
    
    tax_amount = data.price * tax_rate
    seller_receives = data.price - tax_amount
    
    return {
        "price": data.price,
        "tax_rate": tax_rate,
        "tax_rate_percent": f"{tax_rate * 100:.0f}%",
        "tax_amount": round(tax_amount, 4),
        "seller_receives": round(seller_receives, 4)
    }

@api_router.post("/business/{business_id}/sell")
async def sell_business(business_id: str, data: SellBusinessRequest, current_user: User = Depends(get_current_user)):
    """Выставить бизнес с землёй на продажу"""
    # Получаем бизнес
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Получаем пользователя и все его идентификаторы
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        raise HTTPException(status_code=401, detail="User not found")
    
    user = ui["user"]
    user_ids = ui["ids"]
    
    # Проверяем владельца - по всем возможным идентификаторам
    biz_owner = business.get("owner")
    biz_owner_wallet = business.get("owner_wallet")
    
    is_owner = (
        biz_owner in user_ids or
        biz_owner_wallet in user_ids or
        (biz_owner_wallet and biz_owner_wallet == current_user.wallet_address)
    )
    
    if not is_owner:
        raise HTTPException(status_code=403, detail="Это не ваш бизнес")
    
    # Получаем участок
    plot = await db.plots.find_one({"id": business.get("plot_id")}, {"_id": 0})
    if not plot:
        raise HTTPException(status_code=404, detail="Участок не найден")
    
    user_id = user.get("id")
    
    # Проверяем что не на продаже
    existing = await db.land_listings.find_one({
        "plot_id": plot["id"],
        "status": "active"
    })
    if existing:
        raise HTTPException(status_code=400, detail="This property is already listed for sale")
    
    # Минимальная цена
    biz_config = BUSINESSES.get(business.get("business_type"), {})
    base_value = biz_config.get("base_cost_ton", 5) * business.get("level", 1)
    min_price = base_value * 0.5 + (plot.get("price", 0) * 0.5)
    
    if data.price < min_price:
        raise HTTPException(status_code=400, detail=f"Minimum price: {min_price:.2f} TON")
    
    # Рассчитываем налог для отображения
    tax = data.price * RESALE_COMMISSION
    seller_receives = data.price - tax
    
    # Получаем город
    city = await db.cities.find_one({"id": plot.get("city_id")}, {"_id": 0, "name": 1})
    
    # Создаём листинг
    listing = {
        "id": str(uuid.uuid4()),
        "plot_id": plot["id"],
        "business_id": business_id,
        "city_id": plot.get("city_id"),
        "city_name": city.get("name") if city else "Unknown",
        "x": plot.get("x"),
        "y": plot.get("y"),
        "seller_id": current_user.wallet_address,
        "seller_user_id": user_id,
        "seller_username": user.get("username", "Anonymous"),
        "price": data.price,
        "tax_amount": round(tax, 4),
        "seller_receives": round(seller_receives, 4),
        "business": {
            "type": business.get("business_type"),
            "level": business.get("level", 1),
            "durability": business.get("durability", 100),
            "xp": business.get("xp", 0),
            "icon": biz_config.get("icon", "🏢"),
            "name": biz_config.get("name", {})
        },
        "original_plot_price": plot.get("price", 0),
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.land_listings.insert_one(listing.copy())
    
    # Mark business as on_sale
    await db.businesses.update_one(
        {"id": business_id},
        {"$set": {"on_sale": True, "listing_id": listing["id"], "status": "on_sale"}}
    )
    
    # Mark plot as on_sale
    await db.plots.update_one(
        {"id": plot["id"]},
        {"$set": {"on_sale": True, "listing_id": listing["id"]}}
    )
    
    logger.info(f"Business sale listing created: {business_id} @ {data.price} TON")
    
    return {
        "status": "listed",
        "listing": listing,
        "message": f"После продажи вы получите {seller_receives:.4f} TON (налог {tax:.4f} TON)"
    }


@api_router.get("/business/{business_id}/resource-status")
async def check_business_resources(business_id: str, current_user: User = Depends(get_current_user)):
    """Проверить статус ресурсов бизнеса"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    biz_type = business.get("business_type")
    level = business.get("level", 1)
    
    # Получаем доступные ресурсы пользователя из склада
    storage = business.get("storage", {})
    available_resources = storage.get("items", {})
    
    # Проверяем требования
    status = check_resource_requirements(biz_type, level, available_resources)
    
    config = BUSINESSES.get(biz_type, {})
    
    return {
        "business_id": business_id,
        "business_type": biz_type,
        "level": level,
        "consumes": config.get("consumes", []),
        "can_operate": status["can_operate"],
        "missing_resources": status["missing"],
        "reason": status["reason"],
        "storage": available_resources
    }


# ==================== WITHDRAWAL ROUTES ====================

@api_router.post("/withdraw")
async def create_withdraw(
    data: WithdrawRequest,
    current_user: User = Depends(get_current_user)
):
    # Search user by wallet_address or email
    user = None
    if current_user.wallet_address:
        user = await db.users.find_one({"wallet_address": current_user.wallet_address})
    if not user and current_user.email:
        user = await db.users.find_one({"email": current_user.email})
    if not user:
        user = await db.users.find_one({"id": current_user.id})

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Check 2FA requirement
    totp_secret = user.get("two_factor_secret") or user.get("totp_secret")
    is_2fa_enabled = user.get("is_2fa_enabled", False)
    has_passkey = user.get("passkeys") and len(user.get("passkeys", [])) > 0
    
    if not is_2fa_enabled and not has_passkey:
        raise HTTPException(status_code=400, detail="Для вывода средств необходимо включить 2FA аутентификацию в настройках безопасности")
    
    # Verify 2FA code if user has TOTP enabled
    if is_2fa_enabled and totp_secret:
        if not data.totp_code:
            raise HTTPException(status_code=400, detail="Введите код 2FA для подтверждения вывода")
        
        import pyotp
        totp = pyotp.TOTP(totp_secret)
        if not totp.verify(data.totp_code, valid_window=1):
            raise HTTPException(status_code=400, detail="Неверный код 2FA")
    
    # Check if user has a wallet connected
    wallet_address = user.get("wallet_address")
    if not wallet_address:
        raise HTTPException(status_code=400, detail="Подключите кошелёк для вывода средств")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Некорректная сумма")

    if user.get("balance_ton", 0) < data.amount:
        raise HTTPException(status_code=400, detail="Недостаточно средств")

    commission = round(data.amount * WITHDRAWAL_COMMISSION, 6)
    net_amount = round(data.amount - commission, 6)

    display_address = wallet_address
    raw_address = user.get("raw_address") or wallet_address

    withdrawal = {
        "id": str(uuid.uuid4()),
        "tx_type": "withdrawal",
        "user_id": user.get("id"),
        "user_username": user.get("username"),
        "user_wallet": wallet_address,
        "user_raw_address": raw_address,
        "to_address": raw_address,
        "to_address_display": display_address,
        "from_address_display": display_address,
        "amount_ton": data.amount,
        "commission": commission,
        "net_amount": net_amount,
        "status": "pending",
        "tx_hash": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # 🔒 БЛОКИРУЕМ СРЕДСТВА - search by email or wallet
    user_filter = get_user_filter(user)
    await db.users.update_one(
        user_filter,
        {"$inc": {"balance_ton": -data.amount}}
    )

    await db.transactions.insert_one({**withdrawal, "tx_type": "withdrawal"})

    return {
        "status": "pending",
        "withdrawal_id": withdrawal["id"],
        "net_amount": net_amount,
        "to_address": display_address,
        "to_address_raw": raw_address
    }

@api_router.post("/admin/withdrawals/{withdraw_id}/reject")
async def reject_withdrawal(
    withdraw_id: str, 
    admin: User = Depends(get_current_admin)
):
    # 1. Ищем заявку
    withdrawal = await db.withdrawals.find_one({"id": withdraw_id})
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if withdrawal["status"] != "pending":
        raise HTTPException(status_code=400, detail="Можно отклонить только заявку в статусе pending")

    # 2. ВОЗВРАЩАЕМ ДЕНЬГИ ПОЛЬЗОВАТЕЛЮ
    # Важно: используем поле balance_ton и полную сумму (amount)
    await db.users.update_one(
        {"wallet_address": withdrawal["user_wallet"]},
        {"$inc": {"balance_ton": withdrawal["amount"]}}
    )

    # 3. Обновляем статус заявки
    await db.withdrawals.update_one(
        {"id": withdraw_id},
        {
            "$set": {
                "status": "rejected",
                "rejected_at": datetime.now(timezone.utc).isoformat(),
                "admin_id": str(admin.id)
            }
        }
    )

    # 4. Также обновляем в коллекции транзакций (если используешь её для истории)
    await db.transactions.update_one(
        {"id": withdraw_id},
        {"$set": {"status": "rejected"}}
    )

    return {"status": "success", "msg": "Заявка отклонена, средства возвращены пользователю"}

# ==================== STATS ROUTES ====================

@api_router.get("/stats")
async def get_game_stats():
    """Get overall game statistics"""
    # Count from old collections
    owned_plots_old = await db.plots.count_documents({"is_available": False})
    total_businesses_old = await db.businesses.count_documents({})
    
    # Also count from island cells (TON Island)
    island = await db.islands.find_one({"id": "ton_island"})
    owned_plots_island = 0
    businesses_island = 0
    
    if island and 'cells' in island:
        for cell in island['cells']:
            if cell.get('owner'):
                owned_plots_island += 1
            if cell.get('business'):
                businesses_island += 1
    
    # Combine counts
    owned_plots = owned_plots_old + owned_plots_island
    total_businesses = total_businesses_old + businesses_island
    
    total_users = await db.users.count_documents({})
    
    # Calculate TON in circulation - sum of all positive user balances
    pipeline = [
        {"$match": {"balance_ton": {"$gt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": "$balance_ton"}}}
    ]
    balance_result = await db.users.aggregate(pipeline).to_list(1)
    total_balance = balance_result[0]["total"] if balance_result else 0
    
    admin_stats = await db.admin_stats.find_one({"type": "treasury"}, {"_id": 0})
    
    total_plots = max(10000, len(island.get('cells', [])) if island else 0)
    
    return {
        "total_plots": total_plots,
        "owned_plots": owned_plots,
        "available_plots": total_plots - owned_plots,
        "total_businesses": total_businesses,
        "total_players": total_users,
        "total_volume_ton": max(0, round(total_balance, 2)),  # TON in circulation - only positive
        "treasury": admin_stats or {}
    }


# ==================== SPRITE GENERATION ====================

from sprite_generator import BUILDING_BASE_PROMPTS, generate_building_sprite, get_all_sprites_info, generate_all_sprites

@api_router.get("/sprites/info")
async def get_sprites_info():
    """Get info about available building sprites (21 types x 10 levels = 210 total)"""
    return get_all_sprites_info()

@api_router.post("/sprites/generate/{building_type}/{level}")
async def generate_sprite(building_type: str, level: int = 1, admin: User = Depends(get_current_admin)):
    """Generate a single building sprite for specific type and level (admin only)"""
    
    if building_type not in BUILDING_BASE_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Unknown building type: {building_type}")
    
    if level < 1 or level > 10:
        raise HTTPException(status_code=400, detail="Level must be between 1 and 10")
    
    try:
        filename = f"{building_type}_lvl{level}.png"
        save_path = f"/app/frontend/public/sprites/buildings/{filename}"
        image_bytes = await generate_building_sprite(building_type, level, save_path)
        
        return {
            "status": "success",
            "building_type": building_type,
            "level": level,
            "path": f"/sprites/buildings/{filename}",
            "size_bytes": len(image_bytes)
        }
    except Exception as e:
        logger.error(f"Failed to generate sprite: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/sprites/generate-all")
async def generate_all_sprites_endpoint(background_tasks: BackgroundTasks, admin: User = Depends(get_current_admin)):
    """Generate all 210 building sprites in background (admin only)"""
    
    background_tasks.add_task(generate_all_sprites)
    
    return {
        "status": "started",
        "total_sprites": len(BUILDING_BASE_PROMPTS) * 10,
        "message": "Generating 210 sprites (21 types x 10 levels). Check /api/sprites/info for progress."
    }


# ==================== BUSINESS RESOURCE CHECK ====================

@api_router.post("/businesses/check-resources")
async def check_all_business_resources():
    """
    Check all businesses for resource requirements and stop those without resources.
    This should be called by a scheduled task.
    """
    businesses = await db.businesses.find({}, {"_id": 0}).to_list(1000)
    
    stopped = []
    warnings = []
    
    for biz in businesses:
        biz_type = biz.get("business_type")
        level = biz.get("level", 1)
        storage = biz.get("storage", {})
        available = storage.get("items", {})
        
        status = check_resource_requirements(biz_type, level, available)
        
        if not status["can_operate"]:
            # Stop the business
            await db.businesses.update_one(
                {"id": biz["id"]},
                {"$set": {
                    "is_active": False,
                    "stopped_reason": "missing_resources",
                    "stopped_at": datetime.now(timezone.utc).isoformat(),
                    "missing_resources": status["missing"]
                }}
            )
            stopped.append({
                "business_id": biz["id"],
                "type": biz_type,
                "missing": status["missing"]
            })
        elif status["missing"]:
            warnings.append({
                "business_id": biz["id"],
                "type": biz_type,
                "low_resources": status["missing"]
            })
    
    return {
        "checked": len(businesses),
        "stopped": len(stopped),
        "warnings": len(warnings),
        "stopped_businesses": stopped,
        "warning_businesses": warnings
    }

@api_router.post("/business/{business_id}/restart")
async def restart_business(business_id: str, current_user: User = Depends(get_current_user)):
    """Restart a stopped business after resources are added"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Check ownership
    user = await db.users.find_one({"$or": [
        {"id": current_user.id},
        {"wallet_address": current_user.wallet_address}
    ]}, {"_id": 0})
    user_id = user.get("id")
    
    if business.get("owner") != user_id and business.get("owner") != current_user.wallet_address:
        raise HTTPException(status_code=403, detail="Not your business")
    
    # Check resources again
    storage = business.get("storage", {})
    available = storage.get("items", {})
    status = check_resource_requirements(business.get("business_type"), business.get("level", 1), available)
    
    if not status["can_operate"]:
        raise HTTPException(status_code=400, detail=f"Still missing resources: {status['missing']}")
    
    # Restart
    await db.businesses.update_one(
        {"id": business_id},
        {"$set": {
            "is_active": True,
            "stopped_reason": None,
            "stopped_at": None,
            "missing_resources": None,
            "restarted_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"status": "restarted", "business_id": business_id}

# ==================== V2.0 ECONOMIC ENDPOINTS ====================

@api_router.get("/economy/config")
async def get_economy_config():
    """Get full economy configuration for frontend"""
    return {
        "businesses": {
            biz_type: {
                "name": config.get("name", {}),
                "tier": config.get("tier", 1),
                "produces": config.get("produces"),
                "consumes": config.get("consumes", {}),
                "icon": config.get("icon", "🏢"),
                "description": config.get("description", {}),
                "base_cost_ton": config.get("base_cost_ton", 5),
                "is_patron": config.get("is_patron", False),
                "patron_type": config.get("patron_type"),
            }
            for biz_type, config in BUSINESSES.items()
        },
        "resources": RESOURCE_TYPES,
        "resource_types": RESOURCE_TYPES,
        "tier_taxes": TIER_TAXES,
        "turnover_tax": TURNOVER_TAX_RATE,
        "patron_tax": PATRON_TAX_RATE,
        "maintenance_costs": MAINTENANCE_COSTS,
        "warehouse": WAREHOUSE_CONFIG,
        "midnight_decay_rate": MIDNIGHT_DECAY_RATE,
        "npc_price_floor": NPC_PRICE_FLOOR,
        "npc_price_ceiling": NPC_PRICE_CEILING,
        "monopoly_threshold": MONOPOLY_THRESHOLD,
    }


@api_router.get("/economy/business-levels/{business_type}")
async def get_business_levels(business_type: str, lang: str = "ru"):
    """Get production/consumption data for all 10 levels of a business"""
    if business_type not in BUSINESSES:
        raise HTTPException(status_code=404, detail="Business type not found")
    
    config = BUSINESSES[business_type]
    levels_data = BUSINESS_LEVELS.get(business_type, {})
    
    result = {
        "business_type": business_type,
        "name": config.get("name", {}).get(lang, config.get("name", {}).get("en", business_type)),
        "tier": config.get("tier", 1),
        "produces": config.get("produces"),
        "consumes": config.get("consumes", {}),
        "icon": config.get("icon"),
        "levels": {}
    }
    
    for level in range(1, 11):
        stats = get_business_full_stats(business_type, level)
        if stats:
            result["levels"][level] = stats
    
    return result


@api_router.get("/economy/market-prices")
async def get_market_prices():
    """Get current market prices for all resources"""
    prices_doc = await db.market_prices.find_one({"type": "current"})
    if prices_doc:
        return {
            "prices": prices_doc.get("prices", {}),
            "updated_at": prices_doc.get("updated_at"),
        }
    
    # Return base prices if no market data
    base_prices = {r: d["base_price"] for r, d in RESOURCE_TYPES.items()}
    return {"prices": base_prices, "updated_at": None}


@api_router.get("/economy/snapshots")
async def get_economy_snapshots(limit: int = 24):
    """Get recent economic tick snapshots"""
    snapshots = await db.economic_snapshots.find(
        {"type": "tick_snapshot"},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(length=limit)
    return {"snapshots": snapshots}


@api_router.get("/economy/my-resources")
async def get_my_resources(current_user: User = Depends(get_current_user)):
    """Get player's resource inventory"""
    user = await db.users.find_one(
        {"$or": [{"id": current_user.id}, {"wallet_address": current_user.wallet_address}]},
        {"_id": 0}
    )
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    resources = user.get("resources", {})
    balance = user.get("balance_ton", 0)
    
    # Enrich with resource metadata
    enriched = {}
    for resource_type, amount in resources.items():
        meta = RESOURCE_TYPES.get(resource_type, {})
        enriched[resource_type] = {
            "amount": amount,
            "name_ru": meta.get("name_ru", resource_type),
            "name_en": meta.get("name_en", resource_type),
            "icon": meta.get("icon", "📦"),
            "tier": meta.get("tier", 0),
        }
    
    return {
        "resources": enriched,
        "balance_ton": balance,
        "total_income": user.get("total_income", 0),
    }


@api_router.post("/economy/trade")
async def trade_resource(
    resource: str,
    amount: int,
    price_per_unit: float,
    action: str = "sell",  # "sell" or "buy"
    current_user: User = Depends(get_current_user)
):
    """Trade resources on the market with turnover tax"""
    if resource not in RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid resource type")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if price_per_unit <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive")
    
    user = await db.users.find_one(
        {"$or": [{"id": current_user.id}, {"wallet_address": current_user.wallet_address}]},
        {"_id": 0}
    )
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    total_value = amount * price_per_unit
    turnover_tax = TaxSystem.calculate_turnover_tax(total_value)
    
    if action == "sell":
        # Check if user has enough resources
        current_amount = user.get("resources", {}).get(resource, 0)
        if current_amount < amount:
            raise HTTPException(status_code=400, detail=f"Not enough {resource}: have {current_amount}, need {amount}")
        
        # Check monopoly
        total_on_market = await db.market_orders.count_documents({"resource": resource, "action": "sell"})
        user_orders = await db.market_orders.count_documents({"resource": resource, "action": "sell", "seller": user.get("id") or user.get("wallet_address")})
        market_share = user_orders / max(total_on_market + 1, 1)
        
        monopoly = NPCMarketSystem.check_monopoly(market_share)
        
        # Create sell order
        order = {
            "id": str(uuid.uuid4()),
            "type": "sell",
            "resource": resource,
            "amount": amount,
            "price_per_unit": price_per_unit,
            "total_value": total_value,
            "turnover_tax": turnover_tax["tax"],
            "net_value": turnover_tax["net_amount"],
            "seller": user.get("wallet_address") or user.get("id"),
            "is_monopolist": monopoly["is_monopolist"],
            "market_share": monopoly["market_share"],
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Deduct resources from seller
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$inc": {f"resources.{resource}": -amount}}
        )
        
        await db.market_orders.insert_one(order)
        
        return {
            "order": {k: v for k, v in order.items() if k != "_id"},
            "turnover_tax": turnover_tax,
            "monopoly_warning": monopoly["is_monopolist"],
        }
    
    elif action == "buy":
        # Check balance
        total_cost = total_value + turnover_tax["tax"]
        if user.get("balance_ton", 0) < total_cost:
            raise HTTPException(status_code=400, detail="Недостаточно TON на балансе")
        
        # Find matching sell orders
        sell_orders = await db.market_orders.find({
            "resource": resource,
            "type": "sell",
            "status": "open",
            "price_per_unit": {"$lte": price_per_unit},
        }).sort("price_per_unit", 1).to_list(10)
        
        bought = 0
        total_spent = 0
        
        for order in sell_orders:
            if bought >= amount:
                break
            
            can_buy = min(amount - bought, order["amount"])
            cost = can_buy * order["price_per_unit"]
            
            bought += can_buy
            total_spent += cost
            
            # Update order
            remaining = order["amount"] - can_buy
            if remaining <= 0:
                await db.market_orders.update_one(
                    {"id": order["id"]},
                    {"$set": {"status": "filled", "filled_at": datetime.now(timezone.utc).isoformat()}}
                )
            else:
                await db.market_orders.update_one(
                    {"id": order["id"]},
                    {"$set": {"amount": remaining}}
                )
            
            # Credit seller
            await db.users.update_one(
                {"$or": [{"wallet_address": order["seller"]}, {"id": order["seller"]}]},
                {"$inc": {"balance_ton": cost * (1 - TURNOVER_TAX_RATE)}}
            )
        
        if bought > 0:
            # Deduct from buyer and add resources
            tax_on_purchase = total_spent * TURNOVER_TAX_RATE
            await db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$inc": {
                        "balance_ton": -(total_spent + tax_on_purchase),
                        f"resources.{resource}": bought,
                    }
                }
            )
            
            # Treasury gets taxes
            await db.admin_stats.update_one(
                {"type": "treasury"},
                {"$inc": {"total_turnover_tax": tax_on_purchase}},
                upsert=True
            )
        
        return {
            "bought": bought,
            "total_spent": round(total_spent, 6),
            "turnover_tax_paid": round(total_spent * TURNOVER_TAX_RATE, 6),
            "remaining_needed": amount - bought,
        }
    
    raise HTTPException(status_code=400, detail="Invalid action: use 'sell' or 'buy'")


@api_router.get("/economy/npc-status")
async def get_npc_status():
    """Get NPC intervention status and current market health"""
    prices_doc = await db.market_prices.find_one({"type": "current"})
    market_prices = prices_doc.get("prices", {}) if prices_doc else {}
    
    if not market_prices:
        market_prices = {r: d["base_price"] for r, d in RESOURCE_TYPES.items()}
    
    interventions = []
    for resource, price in market_prices.items():
        intervention = NPCMarketSystem.check_price_intervention(resource, price)
        if intervention:
            interventions.append(intervention)
    
    return {
        "market_prices": market_prices,
        "active_interventions": interventions,
        "price_floor": NPC_PRICE_FLOOR,
        "price_ceiling": NPC_PRICE_CEILING,
    }




async def get_income_table(lang: str = "en"):
    """Get income table for all 21 businesses at all 10 levels (V2.0)
    Uses ESTIMATED_DAILY_INCOME for guaranteed profitable display.
    Tier 1 < Tier 2 < Tier 3 guaranteed.
    """
    result = {}
    
    for biz_type, config in BUSINESSES.items():
        name_dict = config.get("name", {})
        biz_name = name_dict.get(lang, name_dict.get("en", biz_type))
        produces = config.get("produces", "")
        tier = config.get("tier", 1)
        tax_rate = TIER_TAXES.get(tier, 0.15)
        
        # Patronage info
        patron_type = config.get("patron_type")
        patron_effect = get_patron_effect(patron_type, 5) if patron_type else None
        
        result[biz_type] = {
            "name": biz_name,
            "icon": config.get("icon", "🏢"),
            "tier": tier,
            "produces": produces,
            "consumes": list(config.get("consumes", {}).keys()),
            "cost": config.get("base_cost_ton", 5),
            "is_patron": config.get("is_patron", False),
            "patron_type": patron_type,
            "patron_effect": patron_effect,
            "levels": {}
        }
        
        for level in range(1, 11):
            stats = get_business_full_stats(biz_type, level)
            if not stats:
                continue
            
            production = stats["production"]["raw"]
            consumption_total = stats["consumption"]["total"]
            consumption_breakdown = stats["consumption"]["breakdown"]
            maintenance = stats["costs"]["maintenance_daily_ton"]
            
            # Use estimated daily income (guaranteed profitable)
            net_daily = get_estimated_daily_income(biz_type, level)
            
            # Reverse-calculate gross and tax from net
            daily_gross = round(net_daily / (1 - tax_rate) + maintenance, 4)
            daily_tax = round(daily_gross * tax_rate, 4)
            monthly = round(net_daily * 30, 2)
            
            # ROI
            build_cost = config.get("base_cost_ton", 5) * (UPGRADE_COST_MULTIPLIER ** (level - 1))
            roi_days = round(build_cost / net_daily, 1) if net_daily > 0 else 999
            
            result[biz_type]["levels"][f"L{level}"] = {
                "level": level,
                "production": production,
                "consumption_total": consumption_total,
                "consumption_breakdown": consumption_breakdown,
                "gross_daily_ton": round(daily_gross, 4),
                "tax_daily_ton": round(daily_tax, 4),
                "maintenance_daily_ton": maintenance,
                "net_daily_ton": round(net_daily, 4),
                "monthly_ton": monthly,
                "roi_days": roi_days,
                "upgrade_cost": stats["costs"]["upgrade"],
                "storage_capacity": stats["storage_capacity"],
                "daily_wear_pct": round(stats["daily_wear"] * 100, 2),
            }
    
    return {"income_table": result}

@api_router.get("/stats/income-table")
async def get_income_table_endpoint(lang: str = "en"):
    """Get income table for all 21 businesses at all 10 levels (V2.0)"""
    return await get_income_table(lang)

@api_router.get("/leaderboard")
async def get_leaderboard():
    """Get top players"""
    pipeline = [
        {"$sort": {"total_income": -1}},
        {"$limit": 20},
        {"$project": {
            "_id": 0,
            "wallet_address": 1,
            "display_name": 1,
            "level": 1,
            "total_income": 1,
            "total_turnover": 1,
            "plots_count": {"$size": {"$ifNull": ["$plots_owned", []]}},
            "businesses_count": {"$size": {"$ifNull": ["$businesses_owned", []]}}
        }}
    ]
    leaders = await db.users.aggregate(pipeline).to_list(20)
    return {"leaderboard": leaders}



@api_router.get("/wallet-settings/public")
async def get_public_wallet_settings():
    """Get public wallet settings (receiver address for deposits)"""
    settings = await db.game_settings.find_one({"type": "ton_wallet"}, {"_id": 0})
    if not settings:
        return {
            "network": "testnet",
            "receiver_address": "",
            "configured": False
        }
    stored_raw = settings.get("receiver_address", "") or ""
    display = to_user_friendly(stored_raw) or stored_raw
    return {
        "network": settings.get("network", "testnet"),
        "receiver_address": display,
        "receiver_address_raw": stored_raw,
        "configured": bool(stored_raw)
    }

# ==================== TON BLOCKCHAIN ROUTES ====================

@api_router.get("/ton/balance/{address}")
async def get_ton_balance(address: str):
    """Get TON balance for an address"""
    if not validate_ton_address(address):
        raise HTTPException(status_code=400, detail="Invalid TON address")
    
    try:
        balance = await ton_client.get_balance(address)
        return {
            "address": address,
            "balance_ton": balance,
            "balance_nano": int(balance * 1e9)
        }
    except Exception as e:
        logger.error(f"Failed to get balance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch balance")

@api_router.post("/ton/verify-transaction")
async def verify_ton_transaction(
    tx_hash: str,
    expected_amount: float,
    to_address: str,
    current_user: User = Depends(get_current_user)
):
    """Verify a TON transaction on blockchain"""
    try:
        is_valid = await ton_client.verify_transaction(tx_hash, expected_amount, to_address)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Transaction verification failed")
        
        return {
            "valid": True,
            "tx_hash": tx_hash,
            "amount": expected_amount,
            "to_address": to_address,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transaction verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

@api_router.get("/ton/transaction-history/{address}")
async def get_ton_transaction_history(address: str, limit: int = 10):
    """Get transaction history for TON address"""
    if not validate_ton_address(address):
        raise HTTPException(status_code=400, detail="Invalid TON address")
    
    try:
        history = await ton_client.get_transaction_history(address, limit)
        return {"address": address, "transactions": history}
    except Exception as e:
        logger.error(f"Failed to get transaction history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")

# ==================== INCOME COLLECTION ROUTES ====================

@api_router.post("/income/collect-all")
async def collect_all_income(current_user: User = Depends(get_current_user)):
    """Collect income from all user's businesses"""
    try:
        businesses = await db.businesses.find({
            "owner": current_user.wallet_address,
            "is_active": True,
            "building_progress": {"$gte": 100}
        }).to_list(100)
        
        total_collected = 0
        collected_businesses = []
        
        for business in businesses:
            business_id = business["id"]
            business_type = business["business_type"]
            level = business.get("level", 1)
            connections = len(business.get("connected_businesses", []))
            
            # Get last collection
            last_collection_str = business.get("last_collection")
            if isinstance(last_collection_str, str):
                last_collection = datetime.fromisoformat(last_collection_str)
            else:
                last_collection = last_collection_str
            
            # Calculate income
            hours_passed = (datetime.now(timezone.utc) - last_collection).total_seconds() / 3600
            days_passed = hours_passed / 24
            
            # Skip if less than 1 hour
            if hours_passed < 1:
                continue
            
            # Get plot zone
            plot = await db.plots.find_one({"id": business["plot_id"]}, {"_id": 0})
            zone = plot.get("zone", "outskirts") if plot else "outskirts"
            
            income_data = calculate_business_income(business_type, level, zone, connections)
            
            gross_income = income_data["gross"] * days_passed
            tax = income_data["tax"] * days_passed
            net_income = income_data["net"] * days_passed
            
            # Update business
            await db.businesses.update_one(
                {"id": business_id},
                {
                    "$set": {"last_collection": datetime.now(timezone.utc).isoformat()},
                    "$inc": {"xp": int(gross_income * 10)}
                }
            )
            
            total_collected += net_income
            collected_businesses.append({
                "business_id": business_id,
                "business_type": business_type,
                "collected": round(net_income, 4),
                "hours_passed": round(hours_passed, 2)
            })
        
        # Update user balance
        if total_collected > 0:
            await db.users.update_one(
                {"wallet_address": current_user.wallet_address},
                {
                    "$inc": {
                        "balance_ton": total_collected,
                        "total_income": total_collected
                    }
                }
            )
        
        return {
            "total_collected": round(total_collected, 4),
            "businesses_count": len(collected_businesses),
            "businesses": collected_businesses
        }
    except Exception as e:
        logger.error(f"Failed to collect income: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect income")

@api_router.get("/income/pending")
async def get_pending_income(current_user: User = Depends(get_current_user)):
    """Get pending income from all user's businesses without collecting"""
    try:
        businesses = await db.businesses.find({
            "owner": current_user.wallet_address,
            "is_active": True,
            "building_progress": {"$gte": 100}
        }).to_list(100)
        
        total_pending = 0
        pending_businesses = []
        
        for business in businesses:
            business_type = business["business_type"]
            level = business.get("level", 1)
            connections = len(business.get("connected_businesses", []))
            
            # Get last collection
            last_collection_str = business.get("last_collection")
            if isinstance(last_collection_str, str):
                last_collection = datetime.fromisoformat(last_collection_str)
            else:
                last_collection = last_collection_str
            
            # Calculate pending income
            hours_passed = (datetime.now(timezone.utc) - last_collection).total_seconds() / 3600
            days_passed = hours_passed / 24
            
            # Get plot zone
            plot = await db.plots.find_one({"id": business["plot_id"]}, {"_id": 0})
            zone = plot.get("zone", "outskirts") if plot else "outskirts"
            
            income_data = calculate_business_income(business_type, level, zone, connections)
            pending = income_data["net"] * days_passed
            
            total_pending += pending
            pending_businesses.append({
                "business_id": business["id"],
                "business_type": business_type,
                "pending": round(pending, 4),
                "hours_passed": round(hours_passed, 2),
                "income_per_day": income_data["net"]
            })
        
        return {
            "total_pending": round(total_pending, 4),
            "businesses_count": len(pending_businesses),
            "businesses": pending_businesses
        }
    except Exception as e:
        logger.error(f"Failed to get pending income: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending income")


# ==================== ADMIN ROUTES ====================

# System settings (stored in DB)
async def get_system_settings():
    """Get current system settings from DB"""
    settings = await db.system_settings.find_one({"type": "fees"}, {"_id": 0})
    if not settings:
        # Default settings
        settings = {
            "type": "fees",
            "income_tax": 0.10,  # 10% подоходный налог
            "withdrawal_fee": 0.03,  # 3% комиссия вывода
            "resale_commission": 0.15,  # 15% при перепродаже
            "trade_commission": 0.0,  # 0% торговая комиссия (отменена)
            "min_withdrawal": 1.0
        }
        await db.system_settings.insert_one(settings)
    return settings

class FeeSettingsUpdate(BaseModel):
    income_tax: float = None
    withdrawal_fee: float = None
    resale_commission: float = None
    trade_commission: float = None
    min_withdrawal: float = None

@admin_router.get("/settings/fees")
async def admin_get_fee_settings(admin: User = Depends(get_admin_user)):
    """Получить настройки комиссий"""
    settings = await get_system_settings()
    return settings

@admin_router.post("/settings/fees")
async def admin_update_fee_settings(data: FeeSettingsUpdate, admin: User = Depends(get_admin_user)):
    """Обновить настройки комиссий"""
    update_data = {}
    
    if data.income_tax is not None:
        if data.income_tax < 0 or data.income_tax > 0.5:
            raise HTTPException(status_code=400, detail="Налог должен быть от 0% до 50%")
        update_data["income_tax"] = data.income_tax
        
    if data.withdrawal_fee is not None:
        if data.withdrawal_fee < 0 or data.withdrawal_fee > 0.2:
            raise HTTPException(status_code=400, detail="Комиссия вывода должна быть от 0% до 20%")
        update_data["withdrawal_fee"] = data.withdrawal_fee
        
    if data.resale_commission is not None:
        if data.resale_commission < 0 or data.resale_commission > 0.5:
            raise HTTPException(status_code=400, detail="Комиссия перепродажи должна быть от 0% до 50%")
        update_data["resale_commission"] = data.resale_commission
        
    if data.trade_commission is not None:
        if data.trade_commission < 0 or data.trade_commission > 0.2:
            raise HTTPException(status_code=400, detail="Торговая комиссия должна быть от 0% до 20%")
        update_data["trade_commission"] = data.trade_commission
        
    if data.min_withdrawal is not None:
        if data.min_withdrawal < 0.1 or data.min_withdrawal > 100:
            raise HTTPException(status_code=400, detail="Минимальный вывод от 0.1 до 100 TON")
        update_data["min_withdrawal"] = data.min_withdrawal
    
    if update_data:
        await db.system_settings.update_one(
            {"type": "fees"},
            {"$set": update_data},
            upsert=True
        )
        logger.info(f"Admin {admin.username} updated fee settings: {update_data}")
    
    settings = await get_system_settings()
    return {"status": "updated", "settings": settings}

@admin_router.get("/stats")
async def admin_get_stats(admin: User = Depends(get_admin_user)):
    """Get admin statistics"""
    stats = await db.admin_stats.find_one({"type": "treasury"}, {"_id": 0})
    
    # Count by status
    pending_withdrawals = await db.transactions.count_documents({"tx_type": "withdrawal", "status": "pending"})
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"last_login": {"$gte": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()}})
    
    # Revenue breakdown
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$tx_type",
            "total": {"$sum": "$amount_ton"},
            "count": {"$sum": 1}
        }}
    ]
    revenue_breakdown = await db.transactions.aggregate(pipeline).to_list(20)
    
    return {
        "treasury": stats or {},
        "pending_withdrawals": pending_withdrawals,
        "total_users": total_users,
        "active_users_7d": active_users,
        "revenue_breakdown": {r["_id"]: {"total": r["total"], "count": r["count"]} for r in revenue_breakdown}
    }

@admin_router.get("/users")
async def admin_get_users(skip: int = 0, limit: int = 50, admin: User = Depends(get_admin_user)):
    """Get all users for admin"""
    users = await db.users.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.users.count_documents({})
    return {"users": users, "total": total, "skip": skip, "limit": limit}

@admin_router.get("/transactions")
async def admin_get_transactions(skip: int = 0, limit: int = 100, tx_type: str = None, admin: User = Depends(get_admin_user)):
    """Get all transactions for admin"""
    query = {}
    if tx_type:
        query["tx_type"] = tx_type
    
    transactions = await db.transactions.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.transactions.count_documents(query)
    return {"transactions": transactions, "total": total}

@admin_router.post("/withdrawal/approve/{tx_id}")
async def admin_approve_withdrawal(tx_id: str, admin: User = Depends(get_current_admin)):
    # 1. Поиск транзакции
    tx = await db.transactions.find_one({"id": tx_id})
    if not tx:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if tx.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Заявка уже обработана")

    # 2. Поиск пользователя для получения RAW адреса
    user_wallet = tx.get("user_wallet")
    user = await db.users.find_one({"wallet_address": user_wallet})
    if not user or "raw_address" not in user:
        raise HTTPException(status_code=400, detail="RAW адрес пользователя не найден")

    # 3. Подготовка данных для отправки
    destination_raw = user["raw_address"]
    net_amount = float(tx.get("net_amount", 0))
    commission = float(tx.get("commission", 0))
    total_amount = float(tx.get("amount", net_amount + commission))
    seed = os.getenv("TON_WALLET_MNEMONIC")

    if not seed:
        raise HTTPException(status_code=500, detail="Мнемоника не настроена в .env")

    try:
        # 4. ВЫЗОВ НОВОГО МЕТОДА ИЗ ton_integration
        # Обрати внимание: вызываем через ton_client.send_ton_payout
        tx_hash = await ton_client.send_ton_payout(
            dest_address=destination_raw,
            amount_ton=net_amount,
            mnemonics=seed
        )
        
        # 5. Успешное завершение
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.transactions.update_one(
            {"id": tx_id},
            {"$set": {
                "status": "completed", 
                "completed_at": now_iso, 
                "blockchain_hash": tx_hash,
                "from_address": "Система", # Это уберет прочерк слева
                "to_address": user_wallet    # Это гарантирует, что адрес справа будет как в БД
            }}
        )
        
        # Статистика
        await db.admin_stats.update_one(
            {"type": "treasury"},
            {"$inc": {"withdrawal_fees": commission, "total_withdrawals": net_amount, "total_withdrawals_count": 1}},
            upsert=True
        )
        return {"status": "completed", "hash": tx_hash}

    except Exception as e:
        logger.error(f"❌ Ошибка в роуте Approve: {e}")
        # ВОЗВРАТ СРЕДСТВ ПРИ ОШИБКЕ БЛОКЧЕЙНА
        await db.users.update_one(
            {"wallet_address": user_wallet},
            {"$inc": {"balance_ton": total_amount}}
        )
        await db.transactions.update_one(
            {"id": tx_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        raise HTTPException(status_code=502, detail=f"Ошибка сети TON: {str(e)}")
    
@admin_router.post("/withdrawal/reject/{tx_id}")
async def admin_reject_withdrawal(tx_id: str, admin: User = Depends(get_current_admin)):
    """Отклонение заявки с гарантированным возвратом на balance_ton"""
    # 1. Ищем саму транзакцию
    tx = await db.transactions.find_one({"id": tx_id})
    if not tx:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if tx.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Можно отклонить только активную заявку")

    # Получаем данные из транзакции - поддерживаем оба поля amount и amount_ton
    user_address = tx.get("user_wallet") or tx.get("from_address")
    user_id = tx.get("user_id")
    amount_to_return = float(tx.get("amount_ton") or tx.get("amount", 0))

    if amount_to_return <= 0:
        raise HTTPException(status_code=400, detail="Сумма для возврата не указана")

    # 2. ВОЗВРАТ: Ищем пользователя по всем возможным идентификаторам
    or_conditions = []
    if user_id:
        or_conditions.append({"id": user_id})
    if user_address:
        or_conditions.append({"wallet_address": user_address})
        or_conditions.append({"raw_address": user_address})
    
    # Также пробуем по raw_address если он есть отдельным полем
    raw_addr = tx.get("user_raw_address")
    if raw_addr:
        or_conditions.append({"raw_address": raw_addr})
    
    if not or_conditions:
        raise HTTPException(status_code=400, detail="Не найдены идентификаторы пользователя в транзакции")
    
    update_result = await db.users.update_one(
        {"$or": or_conditions},
        {"$inc": {"balance_ton": amount_to_return}}
    )

    # 3. Фиксируем результат в базе
    if update_result.modified_count > 0:
        await db.transactions.update_one(
            {"id": tx_id},
            {
                "$set": {
                    "status": "rejected",
                    "rejected_at": datetime.now(timezone.utc).isoformat(),
                    "admin_note": f"Возвращено {amount_to_return} TON на balance_ton"
                }
            }
        )
        return {"status": "success", "message": f"Возвращено {amount_to_return} TON"}
    else:
        raise HTTPException(status_code=404, detail="Пользователь не найден в базе для возврата")


# Tax Settings
class TaxSettings(BaseModel):
    small_business_tax: float = 5
    medium_business_tax: float = 8
    large_business_tax: float = 10
    land_business_sale_tax: float = 10

@admin_router.get("/settings/tax")
async def get_tax_settings(admin: User = Depends(get_admin_user)):
    """Get tax settings"""
    settings = await db.admin_settings.find_one({"type": "tax_settings"}, {"_id": 0})
    if not settings:
        return {
            "small_business_tax": 5,
            "medium_business_tax": 8,
            "large_business_tax": 10,
            "land_business_sale_tax": 10
        }
    return settings

@admin_router.post("/settings/tax")
async def save_tax_settings(data: TaxSettings, admin: User = Depends(get_admin_user)):
    """Save tax settings"""
    await db.admin_settings.update_one(
        {"type": "tax_settings"},
        {"$set": {
            "type": "tax_settings",
            "small_business_tax": data.small_business_tax,
            "medium_business_tax": data.medium_business_tax,
            "large_business_tax": data.large_business_tax,
            "land_business_sale_tax": data.land_business_sale_tax,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    return {"status": "success"}

# Admin Wallets for deposits
class AdminWallet(BaseModel):
    address: str
    percentage: float = 100
    mnemonic: str = ""

@admin_router.get("/wallets")
async def get_admin_wallets(admin: User = Depends(get_admin_user)):
    """Get admin wallets"""
    wallets = await db.admin_wallets.find({}, {"_id": 0, "mnemonic": 0}).to_list(100)
    return {"wallets": wallets}

@admin_router.post("/wallets")
async def add_admin_wallet(data: AdminWallet, admin: User = Depends(get_admin_user)):
    """Add admin wallet"""
    wallet_id = str(uuid.uuid4())
    wallet = {
        "id": wallet_id,
        "address": data.address,
        "percentage": data.percentage,
        "mnemonic": data.mnemonic,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_wallets.insert_one(wallet)
    return {"wallet": {"id": wallet_id, "address": data.address, "percentage": data.percentage}}

@admin_router.delete("/wallets/{wallet_id}")
async def delete_admin_wallet(wallet_id: str, admin: User = Depends(get_admin_user)):
    """Delete admin wallet"""
    await db.admin_wallets.delete_one({"id": wallet_id})
    return {"status": "deleted"}

# User resource management
class UserResourcesUpdate(BaseModel):
    resources: dict

@admin_router.post("/users/{user_id}/resources")
async def update_user_resources(user_id: str, data: UserResourcesUpdate, admin: User = Depends(get_admin_user)):
    """Update user resources"""
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"resources": data.resources, "resources_updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "success"}

class PromoCreateRequest(BaseModel):
    name: str
    code: str = ""
    amount: float
    max_uses: int = 100

@admin_router.post("/promo/create")
async def admin_create_promo(data: PromoCreateRequest, admin: User = Depends(get_admin_user)):
    """Create promo code"""
    code = data.code.upper().strip() if data.code else data.name.upper().replace(" ", "")
    promo = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "code": code,
        "amount": data.amount,
        "max_uses": data.max_uses,
        "current_uses": 0,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.promos.insert_one(promo)
    promo.pop("_id", None)
    return promo

@admin_router.get("/promos")
async def admin_get_promos(admin: User = Depends(get_admin_user)):
    """Get all promo codes"""
    promos = await db.promos.find({}, {"_id": 0}).to_list(100)
    return {"promos": promos}

@admin_router.post("/announcement")
async def admin_create_announcement(title: str, message: str, lang: str = "all", admin: User = Depends(get_admin_user)):
    """Create announcement"""
    announcement = {
        "id": str(uuid.uuid4()),
        "title": title,
        "message": message,
        "lang": lang,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.announcements.insert_one(announcement)
    
    # Broadcast via WebSocket
    await manager.broadcast({"type": "announcement", "data": announcement})
    
    return announcement

@admin_router.get("/announcements")
async def admin_get_announcements(admin: User = Depends(get_admin_user)):
    """Get all announcements"""
    announcements = await db.announcements.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"announcements": announcements}


@admin_router.post("/trigger-auto-collection")
async def admin_trigger_auto_collection(admin: User = Depends(get_admin_user)):
    """Manually trigger automatic income collection (for testing)"""
    try:
        await trigger_auto_collection_now()
        return {
            "status": "completed",
            "message": "Auto-collection triggered successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to trigger auto-collection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger auto-collection: {str(e)}")

@admin_router.get("/system-events")
async def admin_get_system_events(limit: int = 50, admin: User = Depends(get_admin_user)):
    """Get system events (auto-collections, etc.)"""
    events = await db.system_events.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return {"events": events, "total": len(events)}

@admin_router.get("/withdrawals")
async def admin_get_withdrawals(skip: int = 0, limit: int = 100, status: str = None, admin: User = Depends(get_admin_user)):
    """Get withdrawal requests for admin"""
    query = {"tx_type": "withdrawal"}
    if status:
        query["status"] = status
    
    withdrawals = await db.transactions.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.transactions.count_documents(query)
    
    settings = await db.game_settings.find_one({"type": "ton_wallet"}, {"_id": 0})
    treasury_wallet = settings.get("receiver_address_display", "") if settings else ""
    
    if not treasury_wallet:
        stored_raw = settings.get("receiver_address", "") if settings else ""
        treasury_wallet = stored_raw or ""
    
    for w in withdrawals:
        w["from_address"] = treasury_wallet
        w["from_address_display"] = treasury_wallet
        if "to_address_display" not in w or not w["to_address_display"]:
            w["to_address_display"] = w.get("to_address_display") or w.get("user_wallet")
    
    return {
        "withdrawals": withdrawals, 
        "total": total, 
        "skip": skip, 
        "limit": limit, 
        "treasury_wallet": treasury_wallet
    }

@admin_router.get("/wallet-settings")
async def admin_get_wallet_settings(admin: User = Depends(get_admin_user)):
    """Get current wallet settings for admin panel"""
    settings = await db.game_settings.find_one({"type": "ton_wallet"}, {"_id": 0})
    if not settings:
        return {
            "network": "testnet",
            "receiver_address": "",
            "receiver_address_display": "",
            "configured": False
        }
    raw = settings.get("receiver_address", "") or ""
    display = settings.get("receiver_address_display", raw)
    return {
        "network": settings.get("network", "testnet"),
        "receiver_address": raw,
        "receiver_address_display": display,
        "configured": bool(raw),
    }

@admin_router.post("/wallet-settings")
async def admin_update_wallet_settings(
    network: str,
    receiver_address: Optional[str] = None,
    admin: User = Depends(get_admin_user)
):
    """Update TON wallet settings"""
    if network not in ["testnet", "mainnet"]:
        raise HTTPException(status_code=400, detail="Network must be 'testnet' or 'mainnet'")
    
    # Get current settings to preserve receiver_address if not provided
    current = await db.game_settings.find_one({"type": "ton_wallet"})
    
    raw_addr = ""
    display_addr = ""
    
    if receiver_address:
        if not validate_ton_address(receiver_address):
            raise HTTPException(status_code=400, detail="Invalid TON address")
        
        # Normalize: store canonical raw, compute display
        raw_addr = to_raw(receiver_address)
        display_addr = to_user_friendly(raw_addr) or receiver_address if raw_addr else ""
        
        if not raw_addr:
            raise HTTPException(status_code=400, detail="Failed to parse wallet address")
    elif current:
        # Keep existing address
        raw_addr = current.get("receiver_address", "")
        display_addr = current.get("receiver_address_display", "")
    
    await db.game_settings.update_one(
        {"type": "ton_wallet"},
        {
            "$set": {
                "network": network,
                "receiver_address": raw_addr,
                "receiver_address_display": display_addr,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    logger.info(f"✅ Wallet settings updated: {network}")
    
    return {
        "status": "success",
        "network": network,
        "receiver_address": display_addr,
        "receiver_address_raw": raw_addr
    }

@admin_router.get("/deposits")
async def admin_get_deposits(
    limit: int = 50,
    status: Optional[str] = None,
    admin: User = Depends(get_admin_user)
):
    """Get deposit history"""
    query = {}
    if status:
        query["status"] = status
    
    deposits = await db.deposits.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Get stats
    total_deposits = await db.admin_stats.find_one({"type": "treasury"}, {"_id": 0})
    
    return {
        "deposits": deposits,
        "total": len(deposits),
        "stats": total_deposits or {}
    }

@admin_router.post("/deposits/{tx_hash}/credit")
async def admin_manual_credit_deposit(
    tx_hash: str,
    wallet_address: str,
    amount_ton: float,
    admin: User = Depends(get_admin_user)
):
    """Manually credit a deposit (for pending deposits)"""
    # Check if already processed
    existing = await db.deposits.find_one({"tx_hash": tx_hash})
    if existing and existing.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Deposit already credited")
    
    # Find user
    user = await db.users.find_one({"wallet_address": wallet_address})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Credit balance
    await db.users.update_one(
        {"wallet_address": wallet_address},
        {
            "$inc": {
                "balance_ton": amount_ton,
                "total_deposited": amount_ton
            }
        }
    )
    
    # Update or create deposit record
    if existing:
        await db.deposits.update_one(
            {"tx_hash": tx_hash},
            {
                "$set": {
                    "status": "completed",
                    "credited_at": datetime.now(timezone.utc).isoformat(),
                    "credited_by": admin.wallet_address
                }
            }
        )
    else:
        await db.deposits.insert_one({
            "tx_hash": tx_hash,
            "user_id": user["id"],
            "wallet_address": wallet_address,
            "amount_ton": amount_ton,
            "status": "completed",
            "credited_at": datetime.now(timezone.utc).isoformat(),
            "credited_by": admin.wallet_address,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    logger.info(f"✅ Admin credited {amount_ton} TON to {wallet_address[:8]}...")
    
    return {
        "status": "success",
        "credited": amount_ton,
        "user": wallet_address
    }


@admin_router.get("/revenue-stats")
async def admin_get_revenue_stats(admin: User = Depends(get_admin_user)):
    """Get admin revenue statistics"""
    stats = await db.admin_stats.find_one({"type": "treasury"}, {"_id": 0})
    
    if not stats:
        # Return empty stats
        return {
            "plot_sales_income": 0,
            "total_plot_sales": 0,
            "building_sales_income": 0,
            "total_buildings_sold": 0,
            "withdrawal_fees": 0,
            "total_withdrawals": 0,
            "resource_sales_tax": 0,
            "resource_sales_count": 0,
            "total_deposits": 0,
            "deposits_count": 0
        }
    
    return {
        "plot_sales_income": stats.get("plot_sales_income", 0),
        "total_plot_sales": stats.get("total_plot_sales", 0),
        "building_sales_income": stats.get("building_sales_income", 0),
        "total_buildings_sold": stats.get("total_buildings_sold", 0),
        "withdrawal_fees": stats.get("withdrawal_fees", 0),
        "total_withdrawals": stats.get("total_withdrawals", 0),
        "resource_sales_tax": stats.get("resource_sales_tax", 0),
        "resource_sales_count": stats.get("resource_sales_count", 0),
        "total_deposits": stats.get("total_deposits", 0),
        "deposits_count": stats.get("deposits_count", 0)
    }


# ==================== WEBSOCKET ====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    # Track online user
    online_users.add(user_id)
    last_activity[user_id] = datetime.now(timezone.utc)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                # Update activity
                last_activity[user_id] = datetime.now(timezone.utc)
                await manager.send_personal({"type": "pong"}, user_id)
            
            elif data.get("type") == "subscribe_plot":
                # Subscribe to plot updates
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        online_users.discard(user_id)

# ==================== ONLINE STATS ====================

@api_router.get("/stats/online")
async def get_online_stats():
    """Get online users count (users active in last 5 minutes)"""
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(minutes=5)
    
    # Clean up old entries and count active
    active_count = 0
    to_remove = []
    for user_id, last_time in last_activity.items():
        if isinstance(last_time, str):
            last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        if last_time > threshold:
            active_count += 1
        else:
            to_remove.append(user_id)
    
    for user_id in to_remove:
        online_users.discard(user_id)
        last_activity.pop(user_id, None)
    
    return {"online_count": active_count}

@api_router.post("/stats/heartbeat")
async def heartbeat(current_user: User = Depends(get_current_user)):
    """Update user's last activity timestamp"""
    online_users.add(current_user.wallet_address)
    last_activity[current_user.wallet_address] = datetime.now(timezone.utc)
    return {"status": "ok"}

# ==================== TREASURY STATS ====================

@admin_router.get("/treasury-health")
async def get_treasury_health(admin: User = Depends(get_admin_user)):
    """Get detailed treasury health for warnings"""
    stats = await db.admin_stats.find_one({"type": "treasury"}, {"_id": 0})
    
    # Get pending withdrawals amount
    pending_withdrawals = await db.transactions.find({
        "tx_type": "withdrawal",
        "status": "pending"
    }, {"_id": 0, "amount_ton": 1}).to_list(100)
    
    pending_amount = sum(w.get("amount_ton", 0) for w in pending_withdrawals)
    
    # Get first transaction date to calculate days active
    first_tx = await db.transactions.find_one({}, {"_id": 0, "created_at": 1}, sort=[("created_at", 1)])
    days_active = 1
    if first_tx and first_tx.get("created_at"):
        try:
            first_date = datetime.fromisoformat(first_tx["created_at"].replace('Z', '+00:00'))
            days_active = max(1, (datetime.now(timezone.utc) - first_date).days)
        except:
            pass
    
    return {
        "plot_sales_income": stats.get("plot_sales_income", 0) if stats else 0,
        "building_sales_income": stats.get("building_sales_income", 0) if stats else 0,
        "total_tax": stats.get("total_tax", 0) if stats else 0,
        "withdrawal_fees": stats.get("withdrawal_fees", 0) if stats else 0,
        "total_withdrawals": stats.get("total_withdrawals", 0) if stats else 0,
        "total_deposits": stats.get("total_deposits", 0) if stats else 0,
        "pending_withdrawals_amount": pending_amount,
        "pending_withdrawals_count": len(pending_withdrawals),
        "days_active": days_active
    }

# ==================== MAINTENANCE MODE ====================

class MaintenanceRequest(BaseModel):
    enabled: bool
    scheduled_at: Optional[str] = None  # ISO datetime string for scheduled maintenance

@admin_router.get("/maintenance")
async def get_maintenance_status():
    """Get current maintenance status - public endpoint"""
    maintenance = await db.admin_stats.find_one({"type": "maintenance"}, {"_id": 0})
    if not maintenance:
        return {"enabled": False, "scheduled_at": None, "started_at": None}
    return {
        "enabled": maintenance.get("enabled", False),
        "scheduled_at": maintenance.get("scheduled_at"),
        "started_at": maintenance.get("started_at"),
        "message": maintenance.get("message", "Технические работы")
    }

@admin_router.post("/maintenance")
async def set_maintenance_mode(request: MaintenanceRequest, admin: User = Depends(get_admin_user)):
    """Enable/disable maintenance mode"""
    now = datetime.now(timezone.utc).isoformat()
    
    update_data = {
        "type": "maintenance",
        "enabled": request.enabled,
        "updated_at": now,
        "updated_by": admin.wallet_address or admin.email
    }
    
    if request.enabled:
        if request.scheduled_at:
            update_data["scheduled_at"] = request.scheduled_at
            update_data["started_at"] = None
            logger.info(f"Maintenance scheduled for {request.scheduled_at} by {admin.username}")
        else:
            update_data["scheduled_at"] = None
            update_data["started_at"] = now
            logger.info(f"Maintenance started NOW by {admin.username}")
    else:
        update_data["scheduled_at"] = None
        update_data["started_at"] = None
        update_data["ended_at"] = now
        logger.info(f"Maintenance ended by {admin.username}")
    
    await db.admin_stats.update_one(
        {"type": "maintenance"},
        {"$set": update_data},
        upsert=True
    )
    
    return {"status": "ok", "maintenance": update_data}


# ==================== ADMIN DATA PANEL ====================

@admin_router.get("/players/search")
async def admin_search_players(query: str = "", admin: User = Depends(get_admin_user)):
    """Search players by ID, wallet, username, email"""
    filter_q = {}
    if query:
        filter_q = {"$or": [
            {"id": {"$regex": query, "$options": "i"}},
            {"wallet_address": {"$regex": query, "$options": "i"}},
            {"username": {"$regex": query, "$options": "i"}},
            {"display_name": {"$regex": query, "$options": "i"}},
            {"email": {"$regex": query, "$options": "i"}},
        ]}
    
    users_list = await db.users.find(filter_q, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return {"players": users_list, "total": len(users_list)}


@admin_router.get("/players/{player_id}")
async def admin_get_player_details(player_id: str, admin: User = Depends(get_admin_user)):
    """Get FULL player data including businesses, plots, wallet, devices"""
    user = await db.users.find_one(
        {"$or": [{"id": player_id}, {"wallet_address": player_id}, {"username": player_id}]},
        {"_id": 0}
    )
    if not user:
        raise HTTPException(status_code=404, detail="Player not found")
    
    uid = user.get("id") or user.get("wallet_address")
    
    # Get player's businesses
    businesses = await db.businesses.find(
        {"owner": uid}, {"_id": 0}
    ).to_list(50)
    
    # Get player's plots
    plots = await db.plots.find(
        {"owner": uid}, {"_id": 0}
    ).to_list(50)
    
    # Get player's device info
    device_fp = user.get("device_fingerprint", "")
    same_device_accounts = []
    is_multi = False
    
    if device_fp:
        same_device = await db.users.find(
            {"device_fingerprint": device_fp, "id": {"$ne": uid}},
            {"_id": 0, "id": 1, "username": 1, "display_name": 1, "wallet_address": 1, "created_at": 1}
        ).to_list(20)
        same_device_accounts = same_device
        is_multi = len(same_device) > 0
    
    # Transactions
    recent_txs = await db.transactions.find(
        {"$or": [{"user_wallet": uid}, {"user_id": uid}]},
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    return {
        "user": user,
        "businesses": businesses,
        "businesses_count": len(businesses),
        "plots": plots,
        "plots_count": len(plots),
        "recent_transactions": recent_txs,
        "device_fingerprint": device_fp,
        "same_device_accounts": same_device_accounts,
        "is_multi_account": is_multi,
        "multi_account_warning": "МУЛЬТИАККАУНТ!!!" if is_multi else None,
    }


@admin_router.post("/players/{player_id}/update")
async def admin_update_player(player_id: str, updates: dict, admin: User = Depends(get_admin_user)):
    """Update player data (admin override)"""
    allowed_fields = ["balance_ton", "display_name", "level", "experience", "is_banned", "resources"]
    
    update_data = {}
    for key, value in updates.items():
        if key in allowed_fields:
            update_data[key] = value
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    update_data["admin_modified_at"] = datetime.now(timezone.utc).isoformat()
    update_data["admin_modified_by"] = admin.username or admin.email
    
    result = await db.users.update_one(
        {"$or": [{"id": player_id}, {"wallet_address": player_id}]},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Log admin action
    await db.admin_logs.insert_one({
        "action": "player_update",
        "player_id": player_id,
        "changes": update_data,
        "admin": admin.username or admin.email,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    
    return {"status": "updated", "changes": update_data}


@admin_router.get("/market/prices")
async def admin_get_market_prices(admin: User = Depends(get_admin_user)):
    """Get all resource prices for admin management"""
    prices_doc = await db.market_prices.find_one({"type": "current"})
    prices = prices_doc.get("prices", {}) if prices_doc else {}
    if not prices:
        prices = {r: d["base_price"] for r, d in RESOURCE_TYPES.items()}
    
    enriched = {}
    for resource, price in prices.items():
        meta = RESOURCE_TYPES.get(resource, {})
        enriched[resource] = {
            "current_price": price,
            "base_price": meta.get("base_price", 0.01),
            "name_ru": meta.get("name_ru", resource),
            "icon": meta.get("icon", "📦"),
            "tier": meta.get("tier", 0),
            "min_price": MIN_PRICE_TON,
        }
    
    return {"prices": enriched}


@admin_router.post("/market/prices/update")
async def admin_update_prices(price_updates: dict, admin: User = Depends(get_admin_user)):
    """Admin manually set resource prices"""
    prices_doc = await db.market_prices.find_one({"type": "current"})
    prices = prices_doc.get("prices", {}) if prices_doc else {}
    
    for resource, new_price in price_updates.items():
        if resource in RESOURCE_TYPES:
            prices[resource] = max(MIN_PRICE_TON, float(new_price))
    
    await db.market_prices.update_one(
        {"type": "current"},
        {"$set": {"prices": prices, "updated_at": datetime.now(timezone.utc).isoformat(), "admin_override": True}},
        upsert=True
    )
    
    await db.admin_logs.insert_one({
        "action": "price_update",
        "changes": price_updates,
        "admin": admin.username or admin.email,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    
    return {"status": "prices_updated", "prices": prices}


@admin_router.post("/market/stabilize")
async def admin_stabilize_market(resource: str, target_price: float, admin: User = Depends(get_admin_user)):
    """Deploy NPC stabilizer bot for a resource"""
    if resource not in RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid resource")
    
    target_price = max(MIN_PRICE_TON, target_price)
    
    # Create stabilizer bot order
    bot_order = {
        "id": str(uuid.uuid4()),
        "type": "sell",
        "resource": resource,
        "amount": 1000,
        "price_per_unit": target_price * 1.02,  # Slightly above target
        "seller": "NPC_STABILIZER",
        "seller_name": "TON-City Market",
        "is_npc": True,
        "status": "open",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=40)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    await db.market_orders.insert_one(bot_order)
    
    return {
        "status": "stabilizer_deployed",
        "resource": resource,
        "target_price": target_price,
        "sell_price": target_price * 1.02,
        "expires_in_minutes": 40,
    }


# ==================== TELEGRAM BOT WEBHOOK ====================

class TelegramUpdate(BaseModel):
    update_id: int = 0
    message: dict = None

@api_router.post("/telegram/webhook")
async def telegram_webhook(update: TelegramUpdate):
    """Handle Telegram bot webhook updates"""
    try:
        if not update.message:
            return {"ok": True}
        
        chat_id = update.message.get("chat", {}).get("id")
        text = update.message.get("text", "")
        username = update.message.get("from", {}).get("username", "")
        
        if not chat_id:
            return {"ok": True}
        
        # Handle /start command - link user
        if text.startswith("/start"):
            if username:
                # Store the chat_id mapping
                await db.telegram_mappings.update_one(
                    {"username": username.lower()},
                    {"$set": {
                        "username": username.lower(),
                        "chat_id": chat_id,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }},
                    upsert=True
                )
                
                # Check if user exists with this telegram
                user = await db.users.find_one({"telegram_username": username.lower()})
                
                bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
                if bot_token:
                    import aiohttp
                    msg = "Вы подключены к TON City! Уведомления будут приходить сюда." if user else f"Привяжите @{username} в настройках TON City для получения уведомлений."
                    async with aiohttp.ClientSession() as session:
                        await session.post(
                            f"https://api.telegram.org/bot{bot_token}/sendMessage",
                            json={"chat_id": chat_id, "text": f"🏙️ TON City\n\n{msg}"}
                        )
            
            return {"ok": True}
        
        # Handle /status command
        if text == "/status":
            if username:
                user = await db.users.find_one({"telegram_username": username.lower()}, {"_id": 0, "hashed_password": 0})
                if user:
                    balance = user.get("balance_ton", 0)
                    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
                    if bot_token:
                        import aiohttp
                        msg = f"💰 Баланс: {balance:.2f} TON\n👤 {user.get('username', 'N/A')}"
                        async with aiohttp.ClientSession() as session:
                            await session.post(
                                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                                json={"chat_id": chat_id, "text": f"🏙️ TON City\n\n{msg}"}
                            )
            return {"ok": True}
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"ok": True}

@admin_router.post("/telegram/set-webhook")
async def admin_set_telegram_webhook(bot_token: str, admin: User = Depends(get_admin_user)):
    """Set Telegram bot webhook"""
    import aiohttp
    
    webhook_url = os.environ.get("REACT_APP_BACKEND_URL", "") or "https://ton-merchant-hub.preview.emergentagent.com"
    webhook_url = f"{webhook_url}/api/telegram/webhook"
    
    async with aiohttp.ClientSession() as session:
        res = await session.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json={"url": webhook_url}
        )
        data = await res.json()
    
    if data.get("ok"):
        # Store bot token
        await db.game_settings.update_one(
            {"type": "telegram_settings"},
            {"$set": {"type": "telegram_settings", "bot_token": bot_token, "webhook_url": webhook_url}},
            upsert=True
        )
        # Also save to env for background tasks
        os.environ["TELEGRAM_BOT_TOKEN"] = bot_token
        return {"status": "webhook_set", "url": webhook_url}
    
    raise HTTPException(status_code=400, detail=f"Ошибка: {data.get('description', 'Unknown')}")


# ==================== STARTUP TELEGRAM BOT TOKEN ====================

@app.on_event("startup")
async def load_telegram_token():
    """Load Telegram bot token from DB on startup"""
    try:
        settings = await db.game_settings.find_one({"type": "telegram_settings"}, {"_id": 0})
        if settings and settings.get("bot_token"):
            os.environ["TELEGRAM_BOT_TOKEN"] = settings["bot_token"]
            logger.info("✅ Telegram bot token loaded from DB")
    except:
        pass
async def admin_get_patronage_info(admin: User = Depends(get_admin_user)):
    """Get patronage system info"""
    return {"patronage_effects": PATRONAGE_EFFECTS}


# ==================== CREDIT / LENDING SYSTEM ====================

class CreditSystemRequest(BaseModel):
    collateral_business_id: str
    amount: float
    salary_deduction_percent: float
    lender_type: str = "government"  # "government" or bank_business_id

@api_router.get("/credit/calculate/{business_id}")
async def calculate_max_credit(business_id: str, current_user: User = Depends(get_current_user)):
    """Calculate max credit for a business as collateral"""
    business = await db.businesses.find_one({"id": business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Бизнес не найден")
    
    ui = await get_user_identifiers(current_user)
    if not ui["user"] or not is_owner(business, ui["ids"]):
        raise HTTPException(status_code=403, detail="Это не ваш бизнес")
    
    # Check if already in collateral
    existing = await db.credits.find_one({
        "collateral_business_id": business_id,
        "status": {"$in": ["active", "overdue"]}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Этот бизнес уже в залоге")
    
    # Calculate business value
    biz_type = business.get("business_type", "")
    level = business.get("level", 1)
    config = BUSINESSES.get(biz_type, {})
    base_cost = config.get("base_cost_ton", 5)
    upgrade_mult = UPGRADE_COST_MULTIPLIER
    
    total_value = base_cost
    for lvl in range(2, level + 1):
        total_value += base_cost * (upgrade_mult ** (lvl - 1))
    
    # Add plot value
    plot = await db.plots.find_one({"business_id": business_id}, {"_id": 0})
    plot_value = plot.get("price", 25) if plot else 25
    total_value += plot_value
    
    max_credit = round(total_value * 0.30, 2)
    
    # Get government and bank rates
    gov_settings = await db.game_settings.find_one({"type": "credit_settings"}, {"_id": 0})
    gov_rate = gov_settings.get("government_interest_rate", 0.15) if gov_settings else 0.15
    
    # Get available banks for lending
    banks = await db.businesses.find(
        {"business_type": {"$in": ["gram_bank"]}, "durability": {"$gte": 50}},
        {"_id": 0}
    ).to_list(20)
    
    bank_options = []
    for bank in banks:
        bank_owner = bank.get("owner", "")
        if bank_owner in ui["ids"]:
            continue  # Can't borrow from own bank
        bank_settings = await db.credit_bank_settings.find_one({"bank_id": bank["id"]}, {"_id": 0})
        interest = bank_settings.get("interest_rate", 0.20) if bank_settings else 0.20
        overdue_days = bank_settings.get("overdue_penalty_days", 3) if bank_settings else 3
        bank_options.append({
            "bank_id": bank["id"],
            "bank_name": config.get("name", {}).get("ru", "Банк"),
            "owner": bank_owner,
            "level": bank.get("level", 1),
            "interest_rate": min(interest, 0.40),
            "overdue_penalty_days": overdue_days,
            "max_salary_deduction": 0.25,
        })
    
    return {
        "business_id": business_id,
        "business_type": biz_type,
        "business_level": level,
        "business_value": round(total_value, 2),
        "plot_value": plot_value,
        "max_credit": max_credit,
        "government": {
            "interest_rate": gov_rate,
            "max_salary_deduction": 0.40,
        },
        "banks": bank_options,
    }


@api_router.post("/credit/apply")
async def apply_for_credit(data: CreditSystemRequest, current_user: User = Depends(get_current_user)):
    """Apply for a credit/loan"""
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    user = ui["user"]
    
    # Check existing active loans
    active_loans = await db.credits.count_documents({
        "$or": [{"borrower_id": uid} for uid in ui["ids"]],
        "status": {"$in": ["active", "overdue"]}
    })
    if active_loans >= 3:
        raise HTTPException(status_code=400, detail="Максимум 3 активных кредита")
    
    # Verify collateral business
    business = await db.businesses.find_one({"id": data.collateral_business_id}, {"_id": 0})
    if not business:
        raise HTTPException(status_code=404, detail="Бизнес не найден")
    if not is_owner(business, ui["ids"]):
        raise HTTPException(status_code=403, detail="Это не ваш бизнес")
    
    existing_collateral = await db.credits.find_one({
        "collateral_business_id": data.collateral_business_id,
        "status": {"$in": ["active", "overdue"]}
    })
    if existing_collateral:
        raise HTTPException(status_code=400, detail="Этот бизнес уже в залоге")
    
    # Calculate business value and max credit
    biz_type = business.get("business_type", "")
    level = business.get("level", 1)
    config = BUSINESSES.get(biz_type, {})
    base_cost = config.get("base_cost_ton", 5)
    
    total_value = base_cost
    for lvl in range(2, level + 1):
        total_value += base_cost * (UPGRADE_COST_MULTIPLIER ** (lvl - 1))
    
    plot = await db.plots.find_one({"business_id": data.collateral_business_id}, {"_id": 0})
    plot_value = plot.get("price", 25) if plot else 25
    total_value += plot_value
    
    max_credit = total_value * 0.30
    
    if data.amount <= 0 or data.amount > max_credit:
        raise HTTPException(status_code=400, detail=f"Сумма должна быть от 0.01 до {max_credit:.2f} TON")
    
    # Determine lender type
    is_bank = data.lender_type != "government"
    
    if is_bank:
        bank = await db.businesses.find_one({"id": data.lender_type}, {"_id": 0})
        if not bank or "bank" not in bank.get("business_type", ""):
            raise HTTPException(status_code=400, detail="Указанный банк не найден")
        
        bank_settings = await db.credit_bank_settings.find_one({"bank_id": data.lender_type}, {"_id": 0})
        interest_rate = min(bank_settings.get("interest_rate", 0.20) if bank_settings else 0.20, 0.40)
        overdue_days = bank_settings.get("overdue_penalty_days", 3) if bank_settings else 3
        max_deduction = 0.25
        lender_id = bank.get("owner", "")
        lender_name = f"Банк (Ур. {bank.get('level', 1)})"
    else:
        gov_settings = await db.game_settings.find_one({"type": "credit_settings"}, {"_id": 0})
        interest_rate = gov_settings.get("government_interest_rate", 0.15) if gov_settings else 0.15
        overdue_days = 7
        max_deduction = 0.40
        lender_id = "government"
        lender_name = "Государство"
    
    if data.salary_deduction_percent <= 0 or data.salary_deduction_percent > max_deduction * 100:
        raise HTTPException(status_code=400, detail=f"Процент с зарплаты должен быть от 1% до {int(max_deduction*100)}%")
    
    total_debt = round(data.amount * (1 + interest_rate), 2)
    
    credit = {
        "id": str(uuid.uuid4()),
        "borrower_id": user.get("id", ""),
        "borrower_wallet": user.get("wallet_address", ""),
        "lender_type": "bank" if is_bank else "government",
        "lender_id": lender_id,
        "lender_bank_id": data.lender_type if is_bank else None,
        "lender_name": lender_name,
        "collateral_business_id": data.collateral_business_id,
        "collateral_business_type": biz_type,
        "collateral_value": round(total_value, 2),
        "amount": round(data.amount, 2),
        "interest_rate": interest_rate,
        "total_debt": total_debt,
        "paid": 0.0,
        "remaining": total_debt,
        "salary_deduction_percent": data.salary_deduction_percent / 100,
        "overdue_penalty_days": overdue_days,
        "is_doubled_rate": False,
        "overdue_since": None,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_payment": None,
        "next_payment_due": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    }
    
    await db.credits.insert_one(credit)
    
    # Credit the amount to borrower
    await db.users.update_one(
        get_user_filter(user),
        {"$inc": {"balance_ton": data.amount}}
    )
    
    logger.info(f"Credit issued: {data.amount} TON to {user.get('username')} from {lender_name}")
    
    return {
        "status": "approved",
        "credit_id": credit["id"],
        "amount": credit["amount"],
        "total_debt": credit["total_debt"],
        "interest_rate": interest_rate,
        "salary_deduction": data.salary_deduction_percent,
        "collateral": biz_type,
    }


@api_router.get("/credit/my-loans")
async def get_my_loans(current_user: User = Depends(get_current_user)):
    """Get user's active and past loans"""
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        return {"loans": [], "total_debt": 0}
    
    or_conds = [{"borrower_id": uid} for uid in ui["ids"]]
    or_conds.extend([{"borrower_wallet": uid} for uid in ui["ids"]])
    
    loans = await db.credits.find(
        {"$or": or_conds},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    total_debt = sum(l.get("remaining", 0) for l in loans if l.get("status") in ["active", "overdue"])
    
    return {
        "loans": loans,
        "total_debt": round(total_debt, 2),
        "active_count": sum(1 for l in loans if l.get("status") in ["active", "overdue"]),
    }


@api_router.post("/credit/repay/{credit_id}")
async def repay_credit(credit_id: str, amount: float = 0, current_user: User = Depends(get_current_user)):
    """Early repayment of credit"""
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    user = ui["user"]
    
    credit = await db.credits.find_one({"id": credit_id, "status": {"$in": ["active", "overdue"]}}, {"_id": 0})
    if not credit:
        raise HTTPException(status_code=404, detail="Кредит не найден")
    
    if credit.get("borrower_id") not in ui["ids"] and credit.get("borrower_wallet") not in ui["ids"]:
        raise HTTPException(status_code=403, detail="Это не ваш кредит")
    
    remaining = credit.get("remaining", 0)
    pay_amount = min(amount if amount > 0 else remaining, remaining)
    
    if user.get("balance_ton", 0) < pay_amount:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    
    # Deduct from user
    await db.users.update_one(
        get_user_filter(user),
        {"$inc": {"balance_ton": -pay_amount}}
    )
    
    new_remaining = round(remaining - pay_amount, 2)
    new_paid = round(credit.get("paid", 0) + pay_amount, 2)
    
    update = {
        "$set": {
            "remaining": new_remaining,
            "paid": new_paid,
            "last_payment": datetime.now(timezone.utc).isoformat(),
        }
    }
    
    if new_remaining <= 0:
        update["$set"]["status"] = "paid"
        update["$set"]["remaining"] = 0
    
    await db.credits.update_one({"id": credit_id}, update)
    
    # If bank loan, pay to bank owner
    if credit.get("lender_type") == "bank" and credit.get("lender_id"):
        await db.users.update_one(
            {"$or": [{"id": credit["lender_id"]}, {"wallet_address": credit["lender_id"]}]},
            {"$inc": {"balance_ton": pay_amount}}
        )
    
    return {
        "status": "paid" if new_remaining <= 0 else "partial",
        "paid_amount": pay_amount,
        "remaining": max(0, new_remaining),
    }


@api_router.get("/credit/available-banks")
async def get_credit_banks(current_user: User = Depends(get_current_user)):
    """Get banks available for credit"""
    banks = await db.businesses.find(
        {"business_type": {"$regex": "bank"}, "durability": {"$gte": 50}},
        {"_id": 0}
    ).to_list(20)
    
    result = []
    for bank in banks:
        settings = await db.credit_bank_settings.find_one({"bank_id": bank["id"]}, {"_id": 0})
        result.append({
            "bank_id": bank["id"],
            "owner": bank.get("owner", ""),
            "level": bank.get("level", 1),
            "interest_rate": min(settings.get("interest_rate", 0.20) if settings else 0.20, 0.40),
            "overdue_penalty_days": settings.get("overdue_penalty_days", 3) if settings else 3,
        })
    
    return {"banks": result}


# ==================== PROMO CODE ACTIVATION ====================

class PromoActivateRequest(BaseModel):
    code: str

@api_router.post("/promo/activate")
async def activate_promo_code(
    data: Optional[PromoActivateRequest] = None,
    code: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Activate a promo code and add balance. Accepts code in body or query parameter."""
    # Support both body and query parameter
    promo_code = code
    if data and data.code:
        promo_code = data.code
    if not promo_code:
        raise HTTPException(status_code=400, detail="Код промокода обязателен")
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    promo = await db.promos.find_one({"code": promo_code.upper().strip(), "is_active": True})
    if not promo:
        raise HTTPException(status_code=404, detail="Промокод не найден или неактивен")
    
    if promo.get("current_uses", 0) >= promo.get("max_uses", 1):
        raise HTTPException(status_code=400, detail="Промокод уже использован максимальное количество раз")
    
    # Check if user already used this promo
    user_id = ui["user"].get("id", "")
    used = await db.promo_uses.find_one({"promo_id": promo["id"], "user_id": user_id})
    if used:
        raise HTTPException(status_code=400, detail="Вы уже использовали этот промокод")
    
    amount = promo.get("amount", 0)
    
    # Credit user
    await db.users.update_one(
        get_user_filter(ui["user"]),
        {"$inc": {"balance_ton": amount}}
    )
    
    # Record usage
    await db.promo_uses.insert_one({
        "promo_id": promo["id"],
        "user_id": user_id,
        "amount": amount,
        "used_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Increment usage counter
    await db.promos.update_one(
        {"id": promo["id"]},
        {"$inc": {"current_uses": 1}}
    )
    
    # Log transaction
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "promo_activation",
        "amount": amount,  # Positive - user received money
        "details": {
            "promo_code": promo_code.upper(),
            "promo_name": promo.get("name", "")
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Get new balance
    updated_user = await db.users.find_one(get_user_filter(ui["user"]), {"_id": 0, "balance_ton": 1})
    new_balance = updated_user.get("balance_ton", 0) if updated_user else 0
    
    return {
        "status": "activated",
        "amount": amount,
        "promo_name": promo.get("name", ""),
        "new_balance": new_balance
    }


# ==================== TELEGRAM BINDING ====================

@api_router.post("/auth/link-telegram")
async def link_telegram(telegram_username: str, current_user: User = Depends(get_current_user)):
    """Link Telegram account for notifications"""
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    clean_username = telegram_username.strip().lstrip("@")
    if not clean_username:
        raise HTTPException(status_code=400, detail="Укажите username Telegram")
    
    await db.users.update_one(
        get_user_filter(ui["user"]),
        {"$set": {"telegram_username": clean_username, "telegram_notifications": True}}
    )
    
    return {"status": "linked", "telegram_username": clean_username}


@api_router.post("/auth/unlink-telegram")
async def unlink_telegram(current_user: User = Depends(get_current_user)):
    """Unlink Telegram account"""
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    await db.users.update_one(
        get_user_filter(ui["user"]),
        {"$unset": {"telegram_username": "", "telegram_notifications": ""}}
    )
    
    return {"status": "unlinked"}


# ==================== ADMIN CREDIT MANAGEMENT ====================

@admin_router.get("/credits")
async def admin_get_credits(status: str = None, admin: User = Depends(get_admin_user)):
    """Get all credits/loans with seized building info"""
    query = {}
    if status:
        query["status"] = status
    
    credits = await db.credits.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    
    # Enrich with seized building info
    for credit in credits:
        if credit.get("status") in ["overdue", "seized"]:
            biz_id = credit.get("collateral_business_id")
            if biz_id:
                business = await db.businesses.find_one({"id": biz_id}, {"_id": 0})
                if business:
                    credit["seized_building"] = {
                        "id": biz_id,
                        "type": business.get("type"),
                        "level": business.get("level", 1),
                        "for_sale": business.get("for_sale", False),
                        "sale_price": business.get("sale_price", 0),
                        "current_owner": business.get("owner")
                    }
    
    total_active_debt = sum(c.get("remaining", 0) for c in credits if c.get("status") in ["active", "overdue"])
    total_issued = sum(c.get("amount", 0) for c in credits)
    seized_count = sum(1 for c in credits if c.get("status") == "seized")
    
    return {
        "credits": credits,
        "total_active_debt": round(total_active_debt, 2),
        "total_issued": round(total_issued, 2),
        "active_count": sum(1 for c in credits if c.get("status") in ["active", "overdue"]),
        "seized_count": seized_count,
    }


@admin_router.get("/credit-settings")
async def admin_get_credit_settings(admin: User = Depends(get_admin_user)):
    """Get credit system settings"""
    settings = await db.game_settings.find_one({"type": "credit_settings"}, {"_id": 0})
    return settings or {"type": "credit_settings", "government_interest_rate": 0.15}


@admin_router.post("/credit-settings")
async def admin_update_credit_settings(government_interest_rate: float, admin: User = Depends(get_admin_user)):
    """Update government credit settings"""
    if government_interest_rate < 0.01 or government_interest_rate > 1.0:
        raise HTTPException(status_code=400, detail="Ставка должна быть от 1% до 100%")
    
    await db.game_settings.update_one(
        {"type": "credit_settings"},
        {"$set": {
            "type": "credit_settings",
            "government_interest_rate": government_interest_rate,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True
    )
    
    return {"status": "updated", "government_interest_rate": government_interest_rate}


@admin_router.get("/user-details/{user_id}")
async def admin_get_user_details(user_id: str, admin: User = Depends(get_admin_user)):
    """Get detailed user info: credits, balance, business value"""
    user = await db.users.find_one(
        {"$or": [{"id": user_id}, {"wallet_address": user_id}, {"email": user_id}]},
        {"_id": 0, "hashed_password": 0}
    )
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    uid = user.get("id", "")
    wallet = user.get("wallet_address", "")
    
    # Get businesses
    biz_query = {"$or": [{"owner": uid}]}
    if wallet:
        biz_query["$or"].append({"owner": wallet})
    businesses = await db.businesses.find(biz_query, {"_id": 0}).to_list(50)
    
    total_biz_value = 0
    for biz in businesses:
        biz_type = biz.get("business_type", "")
        level = biz.get("level", 1)
        cfg = BUSINESSES.get(biz_type, {})
        base_cost = cfg.get("base_cost_ton", 5)
        val = base_cost
        for lvl in range(2, level + 1):
            val += base_cost * (UPGRADE_COST_MULTIPLIER ** (lvl - 1))
        total_biz_value += val
    
    # Get credits
    credit_query = {"$or": [{"borrower_id": uid}]}
    if wallet:
        credit_query["$or"].append({"borrower_wallet": wallet})
    credits = await db.credits.find(credit_query, {"_id": 0}).to_list(20)
    
    active_debt = sum(c.get("remaining", 0) for c in credits if c.get("status") in ["active", "overdue"])
    
    return {
        "user": user,
        "balance": user.get("balance_ton", 0),
        "total_business_value": round(total_biz_value, 2),
        "businesses_count": len(businesses),
        "businesses": [{
            "id": b["id"],
            "type": b.get("business_type"),
            "level": b.get("level", 1),
        } for b in businesses],
        "credits": credits,
        "active_debt": round(active_debt, 2),
        "available_withdrawal": max(0, round(user.get("balance_ton", 0) - active_debt, 2)),
    }


# ==================== BUSINESS RECOMMENDATION API ====================

@api_router.get("/recommendations/build")
async def get_build_recommendations(current_user: User = Depends(get_current_user)):
    """Analyze the map and recommend the most demanded business to build.
    Based on supply/demand analysis of existing businesses on the map."""
    
    # Count existing businesses by type
    pipeline = [
        {"$group": {"_id": "$business_type", "count": {"$sum": 1}}}
    ]
    biz_counts_raw = await db.businesses.aggregate(pipeline).to_list(100)
    biz_counts = {item["_id"]: item["count"] for item in biz_counts_raw if item["_id"]}
    
    # Analyze supply/demand for each resource
    resource_supply = {}  # How much is produced
    resource_demand = {}  # How much is consumed
    
    for biz_type, config in BUSINESSES.items():
        count = biz_counts.get(biz_type, 0)
        if count == 0:
            continue
        
        produces = config.get("produces", "")
        consumes = config.get("consumes", {})
        
        # Base production at level 1
        base_prod = BUSINESS_LEVELS.get(biz_type, {}).get("production", {}).get(1, 0)
        resource_supply[produces] = resource_supply.get(produces, 0) + base_prod * count
        
        # Consumption
        base_cons = BUSINESS_LEVELS.get(biz_type, {}).get("consumption", {}).get(1, 0)
        for res_name, ratio in consumes.items():
            resource_demand[res_name] = resource_demand.get(res_name, 0) + base_cons * ratio * count
    
    # Find deficits (demand > supply)
    deficits = {}
    for resource in set(list(resource_supply.keys()) + list(resource_demand.keys())):
        supply = resource_supply.get(resource, 0)
        demand = resource_demand.get(resource, 0)
        deficit = demand - supply
        if deficit > 0:
            deficits[resource] = deficit
    
    # Recommend businesses that produce deficit resources
    recommendations = []
    for biz_type, config in BUSINESSES.items():
        produces = config.get("produces", "")
        tier = config.get("tier", 1)
        existing = biz_counts.get(biz_type, 0)
        
        score = 0
        reason = ""
        
        if produces in deficits:
            score = deficits[produces] * (1 + tier * 0.5)
            reason = f"Дефицит {produces}: спрос превышает предложение"
        elif existing == 0:
            score = 50 * tier
            reason = "Нет ни одного на карте"
        else:
            score = max(0, 10 - existing) * tier
            reason = f"Мало на карте ({existing} шт.)"
        
        if score > 0:
            name_ru = config.get("name", {}).get("ru", biz_type)
            income_l1 = ESTIMATED_DAILY_INCOME.get(biz_type, {}).get(1, 0)
            recommendations.append({
                "business_type": biz_type,
                "name": name_ru,
                "icon": config.get("icon", ""),
                "tier": tier,
                "score": round(score, 1),
                "reason": reason,
                "cost_ton": config.get("base_cost_ton", 0),
                "estimated_daily_income": income_l1,
                "existing_count": existing,
            })
    
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "recommendations": recommendations[:5],
        "total_businesses_on_map": sum(biz_counts.values()),
        "deficits": deficits,
    }

# Public endpoint for users to check maintenance
@api_router.get("/maintenance-status")
async def get_public_maintenance_status():
    """Get maintenance status for users"""
    maintenance = await db.admin_stats.find_one({"type": "maintenance"}, {"_id": 0})
    if not maintenance:
        return {"enabled": False}
    
    enabled = maintenance.get("enabled", False)
    scheduled_at = maintenance.get("scheduled_at")
    started_at = maintenance.get("started_at")
    
    # Check if scheduled maintenance should start
    if enabled and scheduled_at and not started_at:
        try:
            scheduled_time = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) >= scheduled_time:
                # Auto-start scheduled maintenance
                await db.admin_stats.update_one(
                    {"type": "maintenance"},
                    {"$set": {"started_at": datetime.now(timezone.utc).isoformat()}}
                )
                return {"enabled": True, "scheduled_at": scheduled_at, "started_at": datetime.now(timezone.utc).isoformat()}
            else:
                return {"enabled": False, "scheduled_at": scheduled_at}
        except:
            pass
    
    return {
        "enabled": enabled and started_at is not None,
        "scheduled_at": scheduled_at,
        "started_at": started_at,
        "message": maintenance.get("message", "Технические работы")
    }

# ==================== HEALTH ====================

@api_router.get("/")
async def root():
    return {"message": "TON City Builder API", "version": "2.0.0", "websocket": True}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "websocket": True}

# ==================== PUBLIC TAX SETTINGS ====================

@public_router.get("/tax-settings")
async def get_public_tax_settings():
    """Получить публичные настройки налогов"""
    settings = await db.admin_settings.find_one({"type": "tax_settings"}, {"_id": 0})
    if not settings:
        return {
            "small_business_tax": 5,
            "medium_business_tax": 8,
            "large_business_tax": 10,
            "land_business_sale_tax": 10
        }
    return {
        "small_business_tax": settings.get("small_business_tax", 5),
        "medium_business_tax": settings.get("medium_business_tax", 8),
        "large_business_tax": settings.get("large_business_tax", 10),
        "land_business_sale_tax": settings.get("land_business_sale_tax", 10)
    }

# ==================== BUSINESS FINANCIAL MODEL (PUBLIC) ====================

@public_router.get("/business/financial-model")
async def get_business_financial_model():
    """Получить полную финансовую модель всех бизнесов"""
    result = {
        "businesses": {},
        "tier_names": TIER_NAMES,
        "level_multipliers": LEVEL_MULTIPLIERS
    }
    
    for business_type, tier in BUSINESS_TIERS.items():
        result["businesses"][business_type] = {
            "name_ru": BUSINESS_NAMES_RU.get(business_type, business_type),
            "tier": tier,
            "tier_name": TIER_NAMES.get(tier, ""),
            "levels": get_all_levels_info(business_type)
        }
    
    return result

@public_router.get("/business/financial-model/{business_type}")
async def get_business_model_by_type(business_type: str):
    """Получить финансовую модель конкретного бизнеса"""
    if business_type not in BUSINESS_TIERS:
        raise HTTPException(status_code=404, detail="Бизнес не найден")
    
    tier = get_business_tier(business_type)
    
    return {
        "business_type": business_type,
        "name_ru": BUSINESS_NAMES_RU.get(business_type, business_type),
        "tier": tier,
        "tier_name": TIER_NAMES.get(tier, ""),
        "levels": get_all_levels_info(business_type)
    }


# ==================== TELEGRAM INTEGRATION ====================

@api_router.post("/user/link-telegram")
async def link_telegram(chat_id: str, current_user: User = Depends(get_current_user)):
    """Link Telegram chat_id to user account for notifications"""
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        raise HTTPException(status_code=401, detail="User not found")
    
    await db.users.update_one(
        get_user_filter(ui["user"]),
        {"$set": {"telegram_chat_id": chat_id}}
    )
    
    return {"status": "linked", "chat_id": chat_id}

@api_router.delete("/user/unlink-telegram")
async def unlink_telegram(current_user: User = Depends(get_current_user)):
    """Unlink Telegram from user account"""
    ui = await get_user_identifiers(current_user)
    if not ui["user"]:
        raise HTTPException(status_code=401, detail="User not found")
    
    await db.users.update_one(
        get_user_filter(ui["user"]),
        {"$unset": {"telegram_chat_id": ""}}
    )
    
    return {"status": "unlinked"}


# Import auth router
from auth_handler import auth_router

# Import security router for 2FA and Passkey
from security.security_router import create_security_router
security_router = create_security_router(db)

# Import business and history routers
from business_system import create_business_router
from transaction_history import create_history_router
business_router = create_business_router(db)
history_router = create_history_router(db)

# Include routers
app.include_router(api_router)
app.include_router(admin_router)
app.include_router(public_router)  # Public endpoints (no auth required)
app.include_router(auth_router, prefix="/api")  # Auth endpoints (/api/auth/...)
app.include_router(chat_router, prefix="/api")  # Chat endpoints (/api/chat/...)
app.include_router(security_router)  # Security endpoints (/api/security/...)
app.include_router(business_router)  # Business system endpoints
app.include_router(history_router)  # Transaction history endpoints

# Initialize chat handler with db
set_chat_db(db)

# WebSocket endpoint for chat
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for real-time chat"""
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    await chat_websocket_handler(websocket, token)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting TON City Builder API...")
    
    # Initialize TON client
    try:
        await init_ton_client()
        logger.info("✅ TON Mainnet client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize TON client: {e}")
    
    # Initialize and start scheduler
    try:
        init_scheduler()
        start_scheduler()
        logger.info("✅ Background task scheduler started")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
    
    # Initialize payment monitor
    try:
        await init_payment_monitor(db)
        logger.info("✅ TON Payment Monitor started")
    except Exception as e:
        logger.error(f"❌ Failed to start payment monitor: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down TON City Builder API...")
    
    # Stop payment monitor
    try:
        await stop_payment_monitor()
        logger.info("✅ Payment monitor stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping payment monitor: {e}")
    
    # Close TON client
    try:
        await close_ton_client()
        logger.info("✅ TON client closed")
    except Exception as e:
        logger.error(f"❌ Error closing TON client: {e}")
    
    # Shutdown scheduler
    try:
        shutdown_scheduler()
        logger.info("✅ Scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}")
    
    # Close MongoDB
    client.close()
    logger.info("✅ MongoDB connection closed")
