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
from tonsdk.utils import Address

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
ADMIN_WALLET = os.environ.get('ADMIN_WALLET') or None
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

# Create the main app
app = FastAPI(title="TON City Builder API")
api_router = APIRouter(prefix="/api")
admin_router = APIRouter(prefix="/api/admin")
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


class WithdrawRequest(BaseModel):
    amount: float

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
                raise HTTPException(status_code=400, detail="Username already taken")
            
            # Проверка уникальности Email (если он прислан)
            if request.email:
                existing_email = await db.users.find_one({"email": request.email})
                if existing_email:
                    print(f"❌ Ошибка: Email {request.email} уже занят")
                    raise HTTPException(status_code=400, detail="Email already registered")

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
                "balance_game": 0.0,
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
        raise HTTPException(status_code=404, detail="User not found")

    raw = user_doc.get("raw_address") or to_raw(user_doc.get("wallet_address") or "")
    display = user_doc.get("wallet_address")

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
        "balance_game": user_doc.get("balance_game", 0.0),
        "total_turnover": user_doc.get("total_turnover", 0.0),
        "total_income": user_doc.get("total_income", 0.0),
        "plots_owned": user_doc.get("plots_owned", []),
        "businesses_owned": user_doc.get("businesses_owned", []),
        "is_admin": user_doc.get("is_admin", False),
        "max_plots": PLAYER_LEVELS.get(user_doc.get("level", "novice"), {}).get("max_plots", 3) if PLAYER_LEVELS else 3
    }

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
        raise HTTPException(status_code=404, detail="Plot not for sale")
    
    if plot["owner"] == current_user.wallet_address:
        raise HTTPException(status_code=400, detail="Cannot buy your own plot")
    
    seller_address = plot["owner"]
    price = plot["price"]
    commission = price * RESALE_COMMISSION  # 15% tax
    seller_amount = price - commission
    
    # Check buyer balance
    buyer = await db.users.find_one({"wallet_address": current_user.wallet_address}, {"_id": 0})
    if buyer["balance_game"] < price:
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
        {"$inc": {"balance_game": -price}, "$push": {"plots_owned": f"{plot['x']},{plot['y']}"}}
    )
    
    # Update seller balance
    await db.users.update_one(
        {"wallet_address": seller_address},
        {"$inc": {"balance_game": seller_amount}, "$pull": {"plots_owned": f"{plot['x']},{plot['y']}"}}
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
    if user["balance_game"] < demolish_cost:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Need {demolish_cost} TON for demolition")
    
    # Deduct demolish cost
    await db.users.update_one(
        {"wallet_address": current_user.wallet_address},
        {"$inc": {"balance_game": -demolish_cost}}
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
async def create_withdraw(
    data: WithdrawRequest,
    current_user: User = Depends(get_current_user)
):
    user = await db.users.find_one(
        {"wallet_address": current_user.wallet_address}
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if user["balance_game"] < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    commission = round(data.amount * WITHDRAWAL_COMMISSION, 6)
    net_amount = round(data.amount - commission, 6)

    display_address = user.get("wallet_address")
    raw_address = user.get("raw_address")

    withdrawal = {
        "id": str(uuid.uuid4()),
        "tx_type": "withdrawal",
        "user_wallet": user["wallet_address"],
        "user_raw_address": raw_address,
        "to_address": raw_address,
        "to_address_display": display_address,
        "from_address_display": display_address,
        "amount_ton": data.amount,
        "commission": commission,
        "net_amount": net_amount,
        "status": "pending",
        "tx_hash": None,
        "created_at": datetime.utcnow().isoformat()
    }

    # 🔒 БЛОКИРУЕМ СРЕДСТВА
    await db.users.update_one(
        {"wallet_address": user["wallet_address"]},
        {"$inc": {"balance_game": -data.amount}}
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
    # Важно: используем поле balance_game и полную сумму (amount)
    await db.users.update_one(
        {"wallet_address": withdrawal["user_wallet"]},
        {"$inc": {"balance_game": withdrawal["amount"]}}
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
            "balance_game": balance,
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
            {"$inc": {"balance_game": total_amount}}
        )
        await db.transactions.update_one(
            {"id": tx_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        raise HTTPException(status_code=502, detail=f"Ошибка сети TON: {str(e)}")
    
@admin_router.post("/withdrawal/reject/{tx_id}")
async def admin_reject_withdrawal(tx_id: str, admin: User = Depends(get_current_admin)):
    """Отклонение заявки с гарантированным возвратом на balance_game"""
    # 1. Ищем саму транзакцию
    tx = await db.transactions.find_one({"id": tx_id})
    if not tx:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if tx.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Можно отклонить только активную заявку")

    # Получаем данные из транзакции
    user_address = tx.get("user_wallet") # Здесь может быть любой формат
    amount_to_return = float(tx.get("amount", 0))

    # 2. ВОЗВРАТ: Ищем пользователя по обоим полям сразу
    # Это гарантирует успех, даже если форматы адресов перемешаны
    update_result = await db.users.update_one(
        {
            "$or": [
                {"wallet_address": user_address},
                {"raw_address": user_address}
            ]
        },
        {"$inc": {"balance_game": amount_to_return}}
    )

    if update_result.modified_count == 0:
        # Если не нашли — пробуем найти по raw_address, если он есть в транзакции отдельным полем
        raw_addr = tx.get("user_raw_address")
        if raw_addr:
            update_result = await db.users.update_one(
                {"raw_address": raw_addr},
                {"$inc": {"balance_game": amount_to_return}}
            )

    # 3. Фиксируем результат в базе
    if update_result.modified_count > 0:
        await db.transactions.update_one(
            {"id": tx_id},
            {
                "$set": {
                    "status": "rejected",
                    "rejected_at": datetime.now(timezone.utc).isoformat(),
                    "admin_note": "Возвращено на balance_game"
                }
            }
        )
        return {"status": "success", "message": f"Возвращено {amount_to_return} TON"}
    else:
        raise HTTPException(status_code=404, detail="Пользователь не найден в базе для возврата")

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
    
    # Normalize: store canonical raw, compute display
    raw_addr = to_raw(receiver_address) if receiver_address else ""
    display_addr = to_user_friendly(raw_addr) or receiver_address if raw_addr else ""
    
    if receiver_address and not raw_addr:
        raise HTTPException(status_code=400, detail="Failed to parse wallet address")
    
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
    
    logger.info(f"✅ Wallet settings updated: {network}, {display_addr[:16]}...")
    
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

# Import auth router
from auth_handler import auth_router

# Include routers
app.include_router(api_router)
app.include_router(admin_router)
app.include_router(auth_router, prefix="/api")  # Auth endpoints (/api/auth/...)

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
