import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# --- КОНФИГУРАЦИЯ ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-2025")
ALGORITHM = "HS256"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")  # Add to .env
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")  # Add to .env

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
auth_router = APIRouter(prefix="/auth", tags=["Auth"])

# --- МОДЕЛИ ДАННЫХ ---
class EmailRegister(BaseModel):
    email: EmailStr
    password: str
    username: str

class EmailLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuth(BaseModel):
    credential: str  # Google ID token

class WalletAuth(BaseModel):
    address: str

class UsernameUpdate(BaseModel):
    username: str


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def generate_avatar_from_initials(name: str) -> str:
    """Генерирует SVG аватар из первых букв имени"""
    if not name:
        name = "U"
    
    # Берем первую букву (или две, если есть пробел)
    parts = name.strip().split()
    if len(parts) >= 2:
        initials = (parts[0][0] + parts[1][0]).upper()
    else:
        initials = name[0].upper()
    
    # Генерируем цвет на основе имени
    hash_val = sum(ord(c) for c in name)
    colors = [
        "#00F0FF",  # cyber-cyan
        "#B026FF",  # neon-purple  
        "#FF6B9D",  # pink
        "#FFB800",  # amber
        "#00FF88",  # green
    ]
    color = colors[hash_val % len(colors)]
    
    # SVG аватар
    svg = f'''<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
        <rect width="100" height="100" fill="{color}"/>
        <text x="50" y="50" font-family="Arial" font-size="40" font-weight="bold" 
              fill="#000" text-anchor="middle" dominant-baseline="central">{initials}</text>
    </svg>'''
    
    return f"data:image/svg+xml;base64,{__import__('base64').b64encode(svg.encode()).decode()}"

def create_token(data: dict):
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Зависимость для получения текущего пользователя (аналог из server.py)
async def get_current_user_local(token: str):
    from server import db
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Ищем либо по почте, либо по адресу кошелька
        user = await db.users.find_one({
            "$or": [
                {"email": user_id},
                {"wallet_address": user_id}
            ]
        })
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# --- ЭНДПОИНТЫ ---

# 1. Регистрация через Email (с Username)
@auth_router.post("/register")
async def register(data: EmailRegister):
    from server import db
    import uuid
    
    # Проверка уникальности
    if await db.users.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    if await db.users.find_one({"username": data.username}):
        raise HTTPException(status_code=400, detail="Этот Username уже занят")
    
    # Генерируем аватар из инициалов
    avatar = generate_avatar_from_initials(data.username)
    
    user = {
        "id": str(uuid.uuid4()),
        "username": data.username,
        "display_name": data.username,
        "email": data.email,
        "hashed_password": pwd_context.hash(data.password),
        "wallet_address": None,
        "raw_address": None,
        "avatar": avatar,
        "balance_game": 0,
        "balance_ton": 0,
        "language": "ru",
        "level": "novice",
        "xp": 0,
        "total_turnover": 0,
        "total_income": 0,
        "plots_owned": [],
        "businesses_owned": [],
        "is_admin": False,
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(user)
    token = create_token({"sub": data.email})
    
    return {
        "token": token,
        "type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "avatar": user["avatar"],
            "display_name": user["display_name"]
        }
    }

# 2. Вход через Email или Username
@auth_router.post("/login")
async def login(data: EmailLogin):
    from server import db
    
    # Поиск пользователя по email ИЛИ username
    user = await db.users.find_one({
        "$or": [
            {"email": data.email},
            {"username": data.email}  # Если передан username в поле email
        ]
    })
    
    if not user or not pwd_context.verify(data.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Неверный Email/Username или пароль")
    
    # Создаем токен с email или username (что есть)
    identifier = user.get("email") or user.get("username")
    token = create_token({"sub": identifier})
    
    # Возвращаем токен и информацию о пользователе
    return {
        "token": token,
        "type": "bearer",
        "user": {
            "id": user.get("id", str(user.get("_id"))),
            "username": user.get("username"),
            "email": user.get("email"),
            "wallet_address": user.get("wallet_address"),
            "avatar": user.get("avatar"),
            "display_name": user.get("display_name") or user.get("username")
        }
    }

# 3. Проверка/Вход через Кошелек (Wallet Check)
@auth_router.post("/wallet-check")
async def wallet_check(data: WalletAuth):
    from server import db
    user = await db.users.find_one({"wallet_address": data.address})
    
    if not user:
        # Если юзера нет, создаем "черновик" без Username
        new_user = {
            "username": None,
            "email": None,
            "wallet_address": data.address,
            "balance_game": 0,
            "created_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(new_user)
        token = create_token({"sub": data.address})
        return {"status": "need_username", "token": token}
    
    # Если юзер есть, но ник почему-то не установлен
    if not user.get("username"):
        token = create_token({"sub": data.address})
        return {"status": "need_username", "token": token}
    
    # Обычный вход
    token = create_token({"sub": data.address})
    return {"status": "ok", "token": token}

# 4. Установка Username (вызывается в модалке после Wallet/Google входа)
@auth_router.post("/set-username")
async def set_username(data: UsernameUpdate, token: str):
    from server import db
    # Получаем юзера по временному токену
    current_user = await get_current_user_local(token)
    
    # Проверяем, свободен ли ник
    if await db.users.find_one({"username": data.username}):
        raise HTTPException(status_code=400, detail="Этот ник уже занят")
    
    if len(data.username) < 3:
        raise HTTPException(status_code=400, detail="Ник слишком короткий")

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"username": data.username}}
    )
    
    return {"status": "success"}