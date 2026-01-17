from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from jose import JWTError, jwt
import math
import asyncio
import json

# Import TON integration and background tasks
from ton_integration import ton_client, init_ton_client, close_ton_client, validate_ton_address
from background_tasks import (
    init_scheduler, start_scheduler, shutdown_scheduler, 
    trigger_auto_collection_now
)
from payment_monitor import init_payment_monitor, stop_payment_monitor

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'ton-city-builder-secret-key-2025')
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'admin-secret-key-2025')
ADMIN_WALLET = os.environ.get('ADMIN_WALLET') or None  # Admin wallet from .env (None if empty)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

# Create the main app
app = FastAPI(title="TON City Builder API")
api_router = APIRouter(prefix="/api")
admin_router = APIRouter(prefix="/api/admin")
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Online users tracking (in-memory, resets on restart)
online_users = set()
last_activity = {}

# ==================== CONSTANTS ====================

# Tax rates
BASE_TAX_RATE = 0.13
PROGRESSIVE_TAX = {0.15: 0.18, 0.20: 0.25, 0.25: 0.35}
RESALE_COMMISSION = 0.15  # 15% tax on resale to prevent speculation
DEMOLISH_COST = 0.05  # 5% of business cost to demolish
TRADE_COMMISSION = 0.0  # No trade commission - income tax applies when user receives money
RENTAL_COMMISSION = 0.10
WITHDRAWAL_COMMISSION = 0.03
MIN_WITHDRAWAL = 1.0

# Level system multipliers
LEVEL_CONFIG = {
    1: {"xp_required": 0, "income_mult": 1.0, "speed_mult": 1.0, "bonus": None},
    2: {"xp_required": 100, "income_mult": 1.2, "speed_mult": 1.1, "bonus": "upgrades"},
    3: {"xp_required": 300, "income_mult": 1.5, "speed_mult": 1.2, "bonus": "discount_5"},
    4: {"xp_required": 600, "income_mult": 1.8, "speed_mult": 1.3, "bonus": "storage"},
    5: {"xp_required": 1000, "income_mult": 2.2, "speed_mult": 1.5, "bonus": "automation_1"},
    6: {"xp_required": 1500, "income_mult": 2.7, "speed_mult": 1.7, "bonus": "discount_10"},
    7: {"xp_required": 2200, "income_mult": 3.3, "speed_mult": 2.0, "bonus": "automation_2"},
    8: {"xp_required": 3000, "income_mult": 4.0, "speed_mult": 2.3, "bonus": "vip"},
    9: {"xp_required": 4000, "income_mult": 5.0, "speed_mult": 2.7, "bonus": "franchise"},
    10: {"xp_required": 5500, "income_mult": 6.5, "speed_mult": 3.0, "bonus": "corporation"},
}

# Player levels
PLAYER_LEVELS = {
    "novice": {"min_turnover": 0, "max_plots": 3, "max_market_share": 0.05},
    "entrepreneur": {"min_turnover": 100, "max_plots": 7, "max_market_share": 0.10},
    "businessman": {"min_turnover": 500, "max_plots": 15, "max_market_share": 0.15},
    "magnate": {"min_turnover": 2000, "max_plots": 30, "max_market_share": 0.20},
    "oligarch": {"min_turnover": 10000, "max_plots": 50, "max_market_share": 0.25},
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
    # Primary sector - Resource production
    "farm": {
        "name": {"en": "Farm", "ru": "Ферма", "zh": "农场"},
        "icon": "🌾",
        "sector": "primary",
        "cost": 5,
        "build_time_hours": 2,
        "materials_required": 50,
        "energy_consumption": 10,
        "produces": "crops",
        "production_rate": 100,  # per hour
        "requires": None,
        "base_income": 2.4,  # TON/day at level 1
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
        "production_rate": 500,  # kWh per hour
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
    "oil_rig": {
        "name": {"en": "Oil Rig", "ru": "Нефтевышка", "zh": "石油钻井"},
        "icon": "🛢️",
        "sector": "primary",
        "cost": 40,
        "build_time_hours": 16,
        "materials_required": 400,
        "energy_consumption": 100,
        "produces": "fuel",
        "production_rate": 30,
        "requires": None,
        "base_income": 8.0,
        "operating_cost": 2.0,
        "allowed_zones": ["industrial", "outskirts"],
        "max_per_player": 3,
        "min_builders": 3,
    },
    "mine": {
        "name": {"en": "Mine", "ru": "Шахта", "zh": "矿山"},
        "icon": "🪨",
        "sector": "primary",
        "cost": 35,
        "build_time_hours": 14,
        "materials_required": 350,
        "energy_consumption": 120,
        "produces": "ore",
        "production_rate": 40,
        "requires": None,
        "base_income": 7.0,
        "operating_cost": 1.8,
        "allowed_zones": ["industrial", "outskirts"],
        "max_per_player": 4,
        "min_builders": 2,
    },
    
    # Secondary sector - Manufacturing
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
    "construction_company": {
        "name": {"en": "Construction Co.", "ru": "Стройкомпания", "zh": "建筑公司"},
        "icon": "🏗️",
        "sector": "secondary",
        "cost": 30,
        "build_time_hours": 12,
        "materials_required": 250,
        "energy_consumption": 100,
        "produces": "construction_service",
        "production_rate": 1,
        "requires": "materials",
        "consumption_rate": 0,  # depends on orders
        "base_income": 5.0,  # varies with orders
        "operating_cost": 1.0,
        "allowed_zones": ["business", "industrial"],
        "max_per_player": 5,
        "min_builders": 2,
    },
    "refinery": {
        "name": {"en": "Refinery", "ru": "НПЗ", "zh": "炼油厂"},
        "icon": "🏭",
        "sector": "secondary",
        "cost": 50,
        "build_time_hours": 20,
        "materials_required": 500,
        "energy_consumption": 150,
        "produces": "refined_fuel",
        "production_rate": 20,
        "requires": "fuel",
        "consumption_rate": 30,
        "base_income": 10.0,
        "operating_cost": 3.0,
        "allowed_zones": ["industrial"],
        "max_per_player": 2,
        "min_builders": 3,
    },
    "steel_mill": {
        "name": {"en": "Steel Mill", "ru": "Сталелитейный", "zh": "钢铁厂"},
        "icon": "🔩",
        "sector": "secondary",
        "cost": 45,
        "build_time_hours": 18,
        "materials_required": 450,
        "energy_consumption": 200,
        "produces": "steel",
        "production_rate": 25,
        "requires": "ore",
        "consumption_rate": 40,
        "base_income": 9.0,
        "operating_cost": 2.5,
        "allowed_zones": ["industrial"],
        "max_per_player": 3,
        "min_builders": 3,
    },
    "textile_factory": {
        "name": {"en": "Textile Factory", "ru": "Текстильная ф-ка", "zh": "纺织厂"},
        "icon": "🧵",
        "sector": "secondary",
        "cost": 20,
        "build_time_hours": 8,
        "materials_required": 180,
        "energy_consumption": 40,
        "produces": "textiles",
        "production_rate": 40,
        "requires": "crops",
        "consumption_rate": 60,
        "base_income": 4.0,
        "operating_cost": 1.2,
        "allowed_zones": ["business", "industrial"],
        "max_per_player": 6,
        "min_builders": 1,
    },
    
    # Tertiary sector - Services
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
        "base_income": 4.8,  # varies by zone
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
        "customer_flow": {"center": 80, "business": 50, "residential": 30},
    },
    "hotel": {
        "name": {"en": "Hotel", "ru": "Отель", "zh": "酒店"},
        "icon": "🏨",
        "sector": "tertiary",
        "cost": 35,
        "build_time_hours": 16,
        "materials_required": 350,
        "energy_consumption": 80,
        "produces": "accommodation",
        "production_rate": 50,  # rooms
        "requires": None,
        "base_income": 8.0,
        "operating_cost": 2.0,
        "allowed_zones": ["center", "business"],
        "max_per_player": 5,
        "min_builders": 2,
        "customer_flow": {"center": 90, "business": 60},
    },
    "hospital": {
        "name": {"en": "Hospital", "ru": "Больница", "zh": "医院"},
        "icon": "🏥",
        "sector": "tertiary",
        "cost": 60,
        "build_time_hours": 24,
        "materials_required": 600,
        "energy_consumption": 150,
        "produces": "healthcare",
        "production_rate": 100,
        "requires": None,
        "base_income": 12.0,
        "operating_cost": 4.0,
        "allowed_zones": ["center", "business", "residential"],
        "max_per_player": 2,
        "min_builders": 3,
    },
    "university": {
        "name": {"en": "University", "ru": "Университет", "zh": "大学"},
        "icon": "🎓",
        "sector": "tertiary",
        "cost": 70,
        "build_time_hours": 30,
        "materials_required": 700,
        "energy_consumption": 100,
        "produces": "education",
        "production_rate": 200,
        "requires": None,
        "base_income": 10.0,
        "operating_cost": 3.0,
        "allowed_zones": ["center", "business"],
        "max_per_player": 1,
        "min_builders": 4,
    },
    "logistics_center": {
        "name": {"en": "Logistics Center", "ru": "Логистический центр", "zh": "物流中心"},
        "icon": "📦",
        "sector": "tertiary",
        "cost": 25,
        "build_time_hours": 10,
        "materials_required": 250,
        "energy_consumption": 60,
        "produces": "logistics",
        "production_rate": 100,
        "requires": None,
        "base_income": 6.0,
        "operating_cost": 1.5,
        "allowed_zones": ["business", "industrial"],
        "max_per_player": 5,
        "min_builders": 2,
    },
    "gas_station": {
        "name": {"en": "Gas Station", "ru": "АЗС", "zh": "加油站"},
        "icon": "⛽",
        "sector": "tertiary",
        "cost": 15,
        "build_time_hours": 6,
        "materials_required": 150,
        "energy_consumption": 20,
        "produces": "fuel_retail",
        "production_rate": 0,
        "requires": "refined_fuel",
        "consumption_rate": 20,
        "base_income": 4.0,
        "operating_cost": 1.0,
        "allowed_zones": ["business", "residential", "industrial", "outskirts"],
        "max_per_player": 8,
        "min_builders": 1,
    },
    
    # Quaternary sector - Finance & Tech
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
    "exchange": {
        "name": {"en": "Exchange", "ru": "Биржа", "zh": "交易所"},
        "icon": "📊",
        "sector": "quaternary",
        "cost": 100,
        "build_time_hours": 48,
        "materials_required": 1000,
        "energy_consumption": 80,
        "produces": "trading",
        "production_rate": 0,
        "requires": None,
        "base_income": 20.0,  # from commissions
        "operating_cost": 3.0,
        "allowed_zones": ["center"],
        "max_per_player": 1,
        "min_builders": 4,
        "max_total": 5,  # max 5 on entire map
    },
    "tech_hub": {
        "name": {"en": "Tech Hub", "ru": "Технопарк", "zh": "科技园"},
        "icon": "💻",
        "sector": "quaternary",
        "cost": 80,
        "build_time_hours": 36,
        "materials_required": 800,
        "energy_consumption": 200,
        "produces": "tech_service",
        "production_rate": 50,
        "requires": None,
        "base_income": 15.0,
        "operating_cost": 4.0,
        "allowed_zones": ["center", "business"],
        "max_per_player": 2,
        "min_builders": 3,
    },
    "data_center": {
        "name": {"en": "Data Center", "ru": "Дата-центр", "zh": "数据中心"},
        "icon": "🖥️",
        "sector": "quaternary",
        "cost": 90,
        "build_time_hours": 40,
        "materials_required": 900,
        "energy_consumption": 500,
        "produces": "data_service",
        "production_rate": 1000,
        "requires": None,
        "base_income": 18.0,
        "operating_cost": 6.0,
        "allowed_zones": ["business", "industrial"],
        "max_per_player": 2,
        "min_builders": 3,
    },
    "insurance": {
        "name": {"en": "Insurance Co.", "ru": "Страховая", "zh": "保险公司"},
        "icon": "🛡️",
        "sector": "quaternary",
        "cost": 40,
        "build_time_hours": 16,
        "materials_required": 400,
        "energy_consumption": 30,
        "produces": "insurance",
        "production_rate": 0,
        "requires": None,
        "base_income": 6.0,
        "operating_cost": 1.0,
        "allowed_zones": ["center", "business"],
        "max_per_player": 2,
        "min_builders": 2,
    },
}

# Resource prices (base)
RESOURCE_PRICES = {
    "crops": 0.001,
    "energy": 0.0002,
    "materials": 0.005,
    "fuel": 0.008,
    "ore": 0.006,
    "goods": 0.004,
    "refined_fuel": 0.015,
    "steel": 0.012,
    "textiles": 0.003,
}

# ==================== MODELS ====================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    display_name: Optional[str] = None
    language: str = "en"
    level: str = "novice"
    xp: int = 0
    balance_ton: float = 0.0
    balance_game: float = 0.0
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
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# Request models
class WalletVerifyRequest(BaseModel):
    address: str
    proof: Optional[Dict[str, Any]] = None
    language: str = "en"

class PurchasePlotRequest(BaseModel):
    plot_x: int
    plot_y: int

class ResalePlotRequest(BaseModel):
    plot_id: str
    price: float

class BuildBusinessRequest(BaseModel):
    plot_id: str
    business_type: str

class CreateContractRequest(BaseModel):
    seller_business_id: str
    buyer_business_id: str
    resource_type: str
    amount_per_hour: float
    price_per_unit: float
    duration_days: int = 7

class TradeResourceRequest(BaseModel):
    seller_business_id: str
    buyer_business_id: str
    resource_type: str
    amount: float

class WithdrawRequest(BaseModel):
    amount: float
    to_address: str

class ConfirmTransactionRequest(BaseModel):
    transaction_id: str
    blockchain_hash: Optional[str] = None

class RentPlotRequest(BaseModel):
    plot_id: str
    rent_price: float

class AcceptRentRequest(BaseModel):
    plot_id: str

# ==================== WEBSOCKET MANAGER ====================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

# ==================== HELPERS ====================

def calculate_plot_price(x: int, y: int) -> tuple:
    """Calculate plot price and zone based on distance from center"""
    center_x, center_y = 50, 50
    distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    # Determine zone
    zone = "outskirts"
    for zone_name, config in ZONES.items():
        if distance <= config["radius_max"]:
            zone = zone_name
            break
    
    # Calculate price
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
        return {"gross": 0, "net": 0}
    
    base_income = bt["base_income"]
    operating_cost = bt["operating_cost"]
    
    # Level multiplier
    level_mult = LEVEL_CONFIG.get(level, LEVEL_CONFIG[1])["income_mult"]
    
    # Zone multiplier for customer-based businesses
    zone_mult = 1.0
    if "customer_flow" in bt and zone in bt["customer_flow"]:
        zone_mult = bt["customer_flow"][zone] / bt["customer_flow"].get("center", 100)
    
    # Connection bonus (+5% per connection)
    connection_mult = 1 + connections * 0.05
    
    gross_income = base_income * level_mult * zone_mult * connection_mult
    net_income = (gross_income - operating_cost * level_mult) * (1 - BASE_TAX_RATE)
    
    return {
        "gross": round(gross_income, 2),
        "operating_cost": round(operating_cost * level_mult, 2),
        "tax": round((gross_income - operating_cost * level_mult) * BASE_TAX_RATE, 2),
        "net": round(net_income, 2),
        "level_mult": level_mult,
        "zone_mult": zone_mult,
        "connection_mult": connection_mult
    }

def get_player_level(turnover: float) -> str:
    """Determine player level based on turnover"""
    for level_name in ["oligarch", "magnate", "businessman", "entrepreneur", "novice"]:
        if turnover >= PLAYER_LEVELS[level_name]["min_turnover"]:
            return level_name
    return "novice"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        wallet_address: str = payload.get("sub")
        if not wallet_address:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_doc = await db.users.find_one({"wallet_address": wallet_address}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Normalize is_admin field to boolean
        if "is_admin" in user_doc:
            if isinstance(user_doc["is_admin"], str):
                user_doc["is_admin"] = user_doc["is_admin"].lower() in ("true", "1", "yes")
            elif not isinstance(user_doc["is_admin"], bool):
                user_doc["is_admin"] = False
        else:
            user_doc["is_admin"] = False
        
        return User(**user_doc)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    user = await get_current_user(credentials)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        wallet_address: str = payload.get("sub")
        if wallet_address:
            user_doc = await db.users.find_one({"wallet_address": wallet_address}, {"_id": 0})
            if user_doc:
                # Normalize is_admin field to boolean
                if "is_admin" in user_doc:
                    if isinstance(user_doc["is_admin"], str):
                        user_doc["is_admin"] = user_doc["is_admin"].lower() in ("true", "1", "yes")
                    elif not isinstance(user_doc["is_admin"], bool):
                        user_doc["is_admin"] = False
                else:
                    user_doc["is_admin"] = False
                return User(**user_doc)
    except:
        pass
    return None

# ==================== TRANSLATIONS ====================

TRANSLATIONS = {
    "en": {
        "welcome": "Welcome to TON City Builder!",
        "plot_purchased": "Plot purchased successfully",
        "business_built": "Business built successfully",
        "insufficient_funds": "Insufficient funds",
        "plot_not_available": "Plot not available",
        "max_plots_reached": "Maximum plots limit reached",
        "invalid_zone": "Business not allowed in this zone",
    },
    "ru": {
        "welcome": "Добро пожаловать в TON City Builder!",
        "plot_purchased": "Участок успешно куплен",
        "business_built": "Бизнес успешно построен",
        "insufficient_funds": "Недостаточно средств",
        "plot_not_available": "Участок недоступен",
        "max_plots_reached": "Достигнут лимит участков",
        "invalid_zone": "Бизнес нельзя построить в этой зоне",
    },
    "zh": {
        "welcome": "欢迎来到TON城市建设者!",
        "plot_purchased": "地块购买成功",
        "business_built": "企业建设成功",
        "insufficient_funds": "资金不足",
        "plot_not_available": "地块不可用",
        "max_plots_reached": "已达到地块上限",
        "invalid_zone": "该区域不允许建设此类企业",
    },
}

def t(key: str, lang: str = "en") -> str:
    """Get translation"""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/verify-wallet")
async def verify_wallet(request: WalletVerifyRequest):
    """Verify wallet connection and create/update user"""
    try:
        wallet_address = request.address
        if not wallet_address:
            raise HTTPException(status_code=400, detail="Wallet address required")
        
        # Check if this is the admin wallet from .env
        is_admin_wallet = bool(ADMIN_WALLET and wallet_address == ADMIN_WALLET)
        
        user_doc = await db.users.find_one({"wallet_address": wallet_address}, {"_id": 0})
        
        if not user_doc:
            new_user = User(wallet_address=wallet_address, language=request.language, is_admin=is_admin_wallet)
            user_dict = new_user.model_dump()
            user_dict['created_at'] = user_dict['created_at'].isoformat()
            user_dict['last_login'] = user_dict['last_login'].isoformat()
            await db.users.insert_one(user_dict.copy())
            user_doc = await db.users.find_one({"wallet_address": wallet_address}, {"_id": 0})
        else:
            update_data = {"last_login": datetime.now(timezone.utc).isoformat(), "language": request.language}
            # Auto-grant admin if this is the admin wallet from .env
            if is_admin_wallet and not user_doc.get("is_admin"):
                update_data["is_admin"] = True
            await db.users.update_one(
                {"wallet_address": wallet_address},
                {"$set": update_data}
            )
            # Refresh user_doc after update
            if is_admin_wallet:
                user_doc = await db.users.find_one({"wallet_address": wallet_address}, {"_id": 0})
        
        # Track online user
        online_users.add(wallet_address)
        last_activity[wallet_address] = datetime.now(timezone.utc)
        
        token = create_access_token(data={"sub": wallet_address})
        
        # Determine if should redirect to admin
        final_is_admin = user_doc.get("is_admin", False) or is_admin_wallet
        
        return {
            "token": token,
            "user": {
                "wallet_address": wallet_address,
                "language": user_doc.get("language", "en"),
                "level": user_doc.get("level", "novice"),
                "balance_ton": user_doc.get("balance_ton", 0),
                "balance_game": user_doc.get("balance_game", 0),
                "plots_owned": user_doc.get("plots_owned", []),
                "businesses_owned": user_doc.get("businesses_owned", []),
                "total_income": user_doc.get("total_income", 0),
                "is_admin": final_is_admin
            },
            "redirect_to_admin": final_is_admin,  # Frontend will use this to redirect
            "message": t("welcome", request.language)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Wallet verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "wallet_address": current_user.wallet_address,
        "display_name": current_user.display_name,
        "language": current_user.language,
        "level": current_user.level,
        "xp": current_user.xp,
        "balance_ton": current_user.balance_ton,
        "balance_game": current_user.balance_game,
        "total_turnover": current_user.total_turnover,
        "total_income": current_user.total_income,
        "plots_owned": current_user.plots_owned,
        "businesses_owned": current_user.businesses_owned,
        "is_admin": current_user.is_admin,
        "max_plots": PLAYER_LEVELS.get(current_user.level, {}).get("max_plots", 3)
    }

@api_router.put("/auth/language")
async def update_language(lang: str, current_user: User = Depends(get_current_user)):
    """Update user language"""
    if lang not in ["en", "ru", "zh"]:
        raise HTTPException(status_code=400, detail="Unsupported language")
    
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$set": {"language": lang}}
    )
    return {"language": lang}

# ==================== PLOTS ROUTES ====================

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
    """Get plot by coordinates"""
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
    
    return {
        **plot,
        "business": business,
        "business_info": BUSINESS_TYPES.get(business["business_type"]) if business else None
    }

@api_router.post("/plots/purchase")
async def purchase_plot(request: PurchasePlotRequest, current_user: User = Depends(get_current_user)):
    """Purchase plot using internal balance"""
    x, y = request.plot_x, request.plot_y
    lang = current_user.language
    
    # Check player limits
    max_plots = PLAYER_LEVELS.get(current_user.level, {}).get("max_plots", 3)
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
    if current_user.balance_game < plot_price:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance. Need {plot_price} TON, have {current_user.balance_game} TON"
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
        {"$inc": {"balance_game": -plot_price}}
    )
    
    # Update plot owner
    await db.plots.update_one(
        {"id": plot["id"]},
        {
            "$set": {
                "owner": current_user.wallet_address,
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
        "new_balance": current_user.balance_game - plot_price,
        "message": f"Plot ({x}, {y}) purchased successfully!"
    }

@api_router.post("/plots/confirm-purchase")
async def confirm_plot_purchase(request: ConfirmTransactionRequest, current_user: User = Depends(get_current_user)):
    """Confirm plot purchase"""
    tx = await db.transactions.find_one({"id": request.transaction_id}, {"_id": 0})
    
    if not tx or tx["from_address"] != current_user.wallet_address:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx["status"] == "completed":
        raise HTTPException(status_code=400, detail="Already completed")
    
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
    """List plot for resale"""
    plot = await db.plots.find_one({"id": request.plot_id}, {"_id": 0})
    
    if not plot or plot.get("owner") != current_user.wallet_address:
        raise HTTPException(status_code=404, detail="Plot not found or not owned")
    
    if plot.get("business_id"):
        raise HTTPException(status_code=400, detail="Cannot sell plot with business")
    
    await db.plots.update_one(
        {"id": request.plot_id},
        {"$set": {"is_available": True, "price": request.price, "is_resale": True}}
    )
    
    return {"status": "listed", "plot_id": request.plot_id, "price": request.price}

@api_router.post("/plots/buy-resale/{plot_id}")
async def buy_resale_plot(plot_id: str, current_user: User = Depends(get_current_user)):
    """Buy a resale plot"""
    plot = await db.plots.find_one({"id": plot_id}, {"_id": 0})
    
    if not plot or not plot.get("is_resale"):
        raise HTTPException(status_code=404, detail="Plot not for sale")
    
    seller_address = plot["owner"]
    price = plot["price"]
    commission = price * RESALE_COMMISSION
    seller_amount = price - commission
    
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
    
    return {
        "transaction_id": tx.id,
        "plot_id": plot_id,
        "amount_ton": price,
        "commission": commission,
        "seller_receives": seller_amount
    }

# ==================== BUSINESS ROUTES ====================

@api_router.get("/businesses/types")
async def get_business_types(lang: str = "en"):
    """Get all available business types"""
    result = {}
    for key, bt in BUSINESS_TYPES.items():
        result[key] = {
            **bt,
            "name": bt["name"].get(lang, bt["name"]["en"]),
            "income_by_level": {
                level: calculate_business_income(key, level, "center", 0)
                for level in range(1, 11)
            }
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
        raise HTTPException(status_code=400, detail="Invalid business type")
    
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
    if current_user.balance_game < total_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Need {total_cost} TON, have {current_user.balance_game} TON"
        )
    
    # Deduct from internal balance
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$inc": {"balance_game": -total_cost}}
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
        "new_balance": current_user.balance_game - total_cost,
        "message": f"{bt['name']['en']} built successfully!"
    }

@api_router.post("/businesses/confirm-build")
async def confirm_business_build(request: ConfirmTransactionRequest, current_user: User = Depends(get_current_user)):
    """Confirm business building after payment"""
    tx = await db.transactions.find_one({"id": request.transaction_id}, {"_id": 0})
    
    if not tx or tx["from_address"] != current_user.wallet_address:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx["status"] == "completed":
        raise HTTPException(status_code=400, detail="Already completed")
    
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
    
    if not business or business["owner"] != current_user.wallet_address:
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
        {"$inc": {"balance_game": net_income, "total_income": net_income}}
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
    base_price = RESOURCE_PRICES.get(request.resource_type, 0.001)
    total_value = request.amount * base_price
    commission = total_value * TRADE_COMMISSION  # Now 0%
    
    # Apply income tax to seller's earnings (13% base rate)
    income_tax = total_value * BASE_TAX_RATE
    seller_receives = total_value - income_tax
    
    # Update seller balance
    await db.users.update_one(
        {"wallet_address": seller_biz["owner"]},
        {"$inc": {"balance_game": seller_receives, "total_income": seller_receives}}
    )
    
    # Update buyer balance (full payment)
    await db.users.update_one(
        {"wallet_address": buyer_biz["owner"]},
        {"$inc": {"balance_game": -total_value}}
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

# ==================== WITHDRAWAL ROUTES ====================

@api_router.post("/withdraw")
async def request_withdrawal(request: WithdrawRequest, current_user: User = Depends(get_current_user)):
    """Request TON withdrawal"""
    if request.amount < MIN_WITHDRAWAL:
        raise HTTPException(status_code=400, detail=f"Minimum withdrawal is {MIN_WITHDRAWAL} TON")
    
    if current_user.balance_game < request.amount:
        raise HTTPException(status_code=400, detail=t("insufficient_funds", current_user.language))
    
    commission = request.amount * WITHDRAWAL_COMMISSION
    net_amount = request.amount - commission
    
    tx = Transaction(
        tx_type="withdrawal",
        from_address=current_user.wallet_address,
        to_address=request.to_address,
        amount_ton=request.amount,
        commission=commission
    )
    tx_dict = tx.model_dump()
    tx_dict['created_at'] = tx_dict['created_at'].isoformat()
    await db.transactions.insert_one(tx_dict.copy())
    
    # Deduct from balance
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$inc": {"balance_game": -request.amount}}
    )
    
    return {
        "transaction_id": tx.id,
        "amount": request.amount,
        "commission": commission,
        "net_amount": net_amount,
        "status": "pending"
    }

# ==================== STATS ROUTES ====================

@api_router.get("/stats")
async def get_game_stats():
    """Get overall game statistics"""
    owned_plots = await db.plots.count_documents({"is_available": False})
    total_businesses = await db.businesses.count_documents({})
    total_users = await db.users.count_documents({})
    
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount_ton"}}}
    ]
    volume_result = await db.transactions.aggregate(pipeline).to_list(1)
    total_volume = volume_result[0]["total"] if volume_result else 0
    
    admin_stats = await db.admin_stats.find_one({"type": "treasury"}, {"_id": 0})
    
    return {
        "total_plots": 10000,
        "owned_plots": owned_plots,
        "available_plots": 10000 - owned_plots,
        "total_businesses": total_businesses,
        "total_players": total_users,
        "total_volume_ton": total_volume,
        "treasury": admin_stats or {}
    }

@api_router.get("/stats/income-table")
async def get_income_table(lang: str = "en"):
    """Get income table for all businesses at all levels"""
    result = {}
    
    for biz_type, bt in BUSINESS_TYPES.items():
        result[biz_type] = {
            "name": bt["name"].get(lang, bt["name"]["en"]),
            "icon": bt["icon"],
            "sector": bt["sector"],
            "cost": bt["cost"],
            "levels": {}
        }
        
        for level in range(1, 11):
            for zone in ["center", "business", "residential", "industrial", "outskirts"]:
                if zone not in bt.get("allowed_zones", ["outskirts"]):
                    continue
                
                for connections in [0, 1, 2, 3, 5]:
                    income = calculate_business_income(biz_type, level, zone, connections)
                    
                    key = f"L{level}_{zone}_C{connections}"
                    result[biz_type]["levels"][key] = {
                        "level": level,
                        "zone": zone,
                        "connections": connections,
                        "gross_daily": income["gross"],
                        "net_daily": income["net"],
                        "monthly": round(income["net"] * 30, 2),
                        "roi_days": round(bt["cost"] / income["net"], 1) if income["net"] > 0 else 999
                    }
    
    return {"income_table": result}

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
    return {
        "network": settings.get("network", "testnet"),
        "receiver_address": settings.get("receiver_address", ""),
        "configured": bool(settings.get("receiver_address"))
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
                        "balance_game": total_collected,
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
async def admin_approve_withdrawal(tx_id: str, admin: User = Depends(get_admin_user)):
    """Approve withdrawal request"""
    tx = await db.transactions.find_one({"id": tx_id, "tx_type": "withdrawal"}, {"_id": 0})
    
    if not tx:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if tx["status"] != "pending":
        raise HTTPException(status_code=400, detail="Not pending")
    
    await db.transactions.update_one(
        {"id": tx_id},
        {"$set": {"status": "approved", "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "approved", "tx_id": tx_id}

@admin_router.post("/withdrawal/reject/{tx_id}")
async def admin_reject_withdrawal(tx_id: str, admin: User = Depends(get_admin_user)):
    """Reject withdrawal request"""
    tx = await db.transactions.find_one({"id": tx_id, "tx_type": "withdrawal"}, {"_id": 0})
    
    if not tx:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    # Refund to user
    await db.users.update_one(
        {"wallet_address": tx["from_address"]},
        {"$inc": {"balance_game": tx["amount_ton"]}}
    )
    
    await db.transactions.update_one(
        {"id": tx_id},
        {"$set": {"status": "rejected", "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "rejected", "tx_id": tx_id, "refunded": tx["amount_ton"]}

@admin_router.post("/user/set-admin/{wallet_address}")
async def admin_set_admin(wallet_address: str, is_admin: bool = True, admin: User = Depends(get_admin_user)):
    """Set user as admin"""
    await db.users.update_one(
        {"wallet_address": wallet_address},
        {"$set": {"is_admin": is_admin}}
    )
    return {"wallet_address": wallet_address, "is_admin": is_admin}

@admin_router.post("/promo/create")
async def admin_create_promo(name: str, amount: float, max_uses: int, admin: User = Depends(get_admin_user)):
    """Create promo code"""
    promo = {
        "id": str(uuid.uuid4()),
        "code": f"TONCITY{uuid.uuid4().hex[:6].upper()}",
        "name": name,
        "amount": amount,
        "max_uses": max_uses,
        "current_uses": 0,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.promos.insert_one(promo)
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



# ==================== ADMIN: TON WALLET SETTINGS ====================

@admin_router.get("/wallet-settings")
async def admin_get_wallet_settings(admin: User = Depends(get_admin_user)):
    """Get TON wallet settings"""
    settings = await db.game_settings.find_one({"type": "ton_wallet"}, {"_id": 0})
    if not settings:
        # Create default
        settings = {
            "type": "ton_wallet",
            "network": "testnet",
            "receiver_address": "",
            "last_checked_lt": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.game_settings.insert_one(settings)
    return settings

@admin_router.post("/wallet-settings")
async def admin_update_wallet_settings(
    network: str,
    receiver_address: str,
    admin: User = Depends(get_admin_user)
):
    """Update TON wallet settings"""
    if network not in ["testnet", "mainnet"]:
        raise HTTPException(status_code=400, detail="Network must be 'testnet' or 'mainnet'")
    
    if receiver_address and not validate_ton_address(receiver_address):
        raise HTTPException(status_code=400, detail="Invalid TON address")
    
    await db.game_settings.update_one(
        {"type": "ton_wallet"},
        {
            "$set": {
                "network": network,
                "receiver_address": receiver_address,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    logger.info(f"✅ Wallet settings updated: {network}, {receiver_address[:8]}...")
    
    return {
        "status": "success",
        "network": network,
        "receiver_address": receiver_address
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
        raise HTTPException(status_code=404, detail="User not found")
    
    # Credit balance
    await db.users.update_one(
        {"wallet_address": wallet_address},
        {
            "$inc": {
                "balance_game": amount_ton,
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
            "total_tax": 0,
            "withdrawal_fees": 0,
            "total_withdrawals": 0,
            "total_deposits": 0,
            "deposits_count": 0
        }
    
    return {
        "plot_sales_income": stats.get("plot_sales_income", 0),
        "total_plot_sales": stats.get("total_plot_sales", 0),
        "building_sales_income": stats.get("building_sales_income", 0),
        "total_buildings_sold": stats.get("total_buildings_sold", 0),
        "total_tax": stats.get("total_tax", 0),
        "withdrawal_fees": stats.get("withdrawal_fees", 0),
        "total_withdrawals": stats.get("total_withdrawals", 0),
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

# ==================== HEALTH ====================

@api_router.get("/")
async def root():
    return {"message": "TON City Builder API", "version": "2.0.0", "websocket": True}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "websocket": True}

# Include routers
app.include_router(api_router)
app.include_router(admin_router)

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
