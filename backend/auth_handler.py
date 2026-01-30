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
    email: str  # Changed from EmailStr to str to allow username
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

# Зависимость для получения текущего пользователя через Bearer token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

async def get_current_user_local(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from server import db
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Ищем по email, username или wallet_address
        user = await db.users.find_one({
            "$or": [
                {"email": user_id},
                {"username": user_id},
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


# 2.5. Вход/Регистрация через Google OAuth
@auth_router.post("/google")
async def google_auth(data: GoogleAuth):
    """
    Аутентификация через Google OAuth
    Принимает Google ID token от фронтенда
    """
    from server import db
    import uuid
    
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Please add GOOGLE_CLIENT_ID to .env"
        )
    
    try:
        # Верифицируем Google ID token
        idinfo = id_token.verify_oauth2_token(
            data.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # Получаем данные пользователя из Google
        email = idinfo.get('email')
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')
        google_id = idinfo.get('sub')
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        # Ищем пользователя по email или google_id
        user = await db.users.find_one({
            "$or": [
                {"email": email},
                {"google_id": google_id}
            ]
        })
        
        if user:
            # Пользователь существует - обновляем данные при необходимости
            updates = {}
            if not user.get("google_id"):
                updates["google_id"] = google_id
            if picture and not user.get("avatar_uploaded"):
                updates["avatar"] = picture
            if not user.get("display_name"):
                updates["display_name"] = name
            
            if updates:
                updates["last_login"] = datetime.now(timezone.utc)
                await db.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": updates}
                )
                user.update(updates)
            
        else:
            # Новый пользователь - создаем аккаунт
            # Генерируем уникальный username из email
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while await db.users.find_one({"username": username}):
                username = f"{base_username}{counter}"
                counter += 1
            
            # Используем Google avatar или генерируем из инициалов
            avatar = picture if picture else generate_avatar_from_initials(name or username)
            
            user = {
                "id": str(uuid.uuid4()),
                "username": username,
                "display_name": name or username,
                "email": email,
                "google_id": google_id,
                "hashed_password": None,  # Google users don't have password
                "wallet_address": None,
                "raw_address": None,
                "avatar": avatar,
                "avatar_uploaded": bool(picture),  # Track if using Google avatar
                "balance_ton": 0,
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
        
        # Создаем токен
        token = create_token({"sub": email})
        
        return {
            "token": token,
            "type": "bearer",
            "user": {
                "id": user.get("id", str(user.get("_id"))),
                "username": user.get("username"),
                "email": user.get("email"),
                "wallet_address": user.get("wallet_address"),
                "avatar": user.get("avatar"),
                "display_name": user.get("display_name")
            }
        }
        
    except ValueError as e:
        # Invalid token
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google auth error: {str(e)}")

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
            "balance_ton": 0,
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


# 5. Настройки пользователя
class UpdateUsernameRequest(BaseModel):
    username: str

class UpdateEmailRequest(BaseModel):
    email: EmailStr
    password: str  # Требуется текущий пароль для подтверждения

class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class LinkWalletRequest(BaseModel):
    wallet_address: str

class UploadAvatarRequest(BaseModel):
    avatar_data: str  # Base64 encoded image or URL

@auth_router.put("/update-username")
async def update_username(data: UpdateUsernameRequest, current_user: dict = Depends(get_current_user_local)):
    """Изменение username"""
    from server import db
    
    if len(data.username) < 3:
        raise HTTPException(status_code=400, detail="Username слишком короткий (минимум 3 символа)")
    
    # Проверяем уникальность
    existing = await db.users.find_one({"username": data.username})
    if existing and str(existing.get("_id")) != str(current_user.get("_id")):
        raise HTTPException(status_code=400, detail="Этот username уже занят")
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"username": data.username, "display_name": data.username}}
    )
    
    return {"status": "success", "username": data.username}

@auth_router.put("/update-email")
async def update_email(data: UpdateEmailRequest, current_user: dict = Depends(get_current_user_local)):
    """Изменение email (требуется пароль)"""
    from server import db
    
    # Проверка: у пользователя должен быть пароль (не Google auth)
    if not current_user.get("hashed_password"):
        raise HTTPException(status_code=400, detail="Невозможно изменить email для аккаунта Google")
    
    # Проверяем текущий пароль
    if not pwd_context.verify(data.password, current_user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Неверный пароль")
    
    # Проверяем уникальность email
    existing = await db.users.find_one({"email": data.email})
    if existing and str(existing.get("_id")) != str(current_user.get("_id")):
        raise HTTPException(status_code=400, detail="Этот email уже используется")
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"email": data.email}}
    )
    
    return {"status": "success", "email": data.email}

@auth_router.put("/update-password")
async def update_password(data: UpdatePasswordRequest, current_user: dict = Depends(get_current_user_local)):
    """Изменение пароля"""
    from server import db
    
    # Проверка: у пользователя должен быть пароль (не Google auth)
    if not current_user.get("hashed_password"):
        raise HTTPException(status_code=400, detail="Невозможно установить пароль для аккаунта Google")
    
    # Проверяем текущий пароль
    if not pwd_context.verify(data.current_password, current_user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Неверный текущий пароль")
    
    # Хешируем новый пароль
    new_hashed = pwd_context.hash(data.new_password)
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"hashed_password": new_hashed}}
    )
    
    return {"status": "success"}

@auth_router.post("/link-wallet")
async def link_wallet(data: LinkWalletRequest, current_user: dict = Depends(get_current_user_local)):
    """Привязка кошелька к аккаунту"""
    from server import db, to_raw
    
    # Проверяем, не привязан ли кошелек к другому аккаунту
    raw_address = to_raw(data.wallet_address)
    existing = await db.users.find_one({
        "$or": [
            {"wallet_address": data.wallet_address},
            {"raw_address": raw_address}
        ]
    })
    
    if existing and str(existing.get("_id")) != str(current_user.get("_id")):
        raise HTTPException(status_code=400, detail="Этот кошелек уже привязан к другому аккаунту")
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "wallet_address": data.wallet_address,
            "raw_address": raw_address
        }}
    )
    
    return {"status": "success", "wallet_address": data.wallet_address}

@auth_router.post("/unlink-wallet")
async def unlink_wallet(current_user: dict = Depends(get_current_user_local)):
    """Отвязка кошелька от аккаунта"""
    from server import db
    
    # Проверяем, есть ли у пользователя email (иначе он потеряет доступ к аккаунту)
    if not current_user.get("email") and not current_user.get("hashed_password"):
        raise HTTPException(
            status_code=400, 
            detail="Невозможно отвязать кошелек - у вас нет email. Сначала добавьте email в настройках."
        )
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$unset": {
            "wallet_address": "",
            "raw_address": ""
        }}
    )
    
    return {"status": "success", "message": "Кошелек отвязан"}

@auth_router.post("/upload-avatar")
async def upload_avatar(data: UploadAvatarRequest, current_user: dict = Depends(get_current_user_local)):
    """Загрузка пользовательского аватара"""
    from server import db
    
    # В реальном приложении здесь была бы загрузка на S3/CDN
    # Пока просто сохраняем base64/URL
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "avatar": data.avatar_data,
            "avatar_uploaded": True
        }}
    )
    
    return {"status": "success", "avatar": data.avatar_data}



# ==================== PASSWORD RESET ====================

class RequestPasswordResetRequest(BaseModel):
    email: EmailStr

class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

@auth_router.post("/request-password-reset")
async def request_password_reset(data: RequestPasswordResetRequest):
    """Запрос сброса пароля - отправляет код на email"""
    from server import db
    from email_service import generate_reset_code, store_reset_code, send_reset_email
    
    # Проверяем существование пользователя
    user = await db.users.find_one({"email": data.email})
    
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    
    # Проверяем что у пользователя есть пароль (не только wallet/google auth)
    if not user.get("hashed_password"):
        raise HTTPException(status_code=400, detail="no_password_account")
    
    # Генерируем и сохраняем код
    code = generate_reset_code()
    store_reset_code(data.email, code)
    
    # Отправляем email
    language = user.get("language", "en")
    email_sent = send_reset_email(data.email, code, language)
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="email_send_failed")
    
    return {"status": "success", "message": "code_sent"}

@auth_router.post("/verify-reset-code")
async def verify_reset_code_endpoint(data: VerifyResetCodeRequest):
    """Проверка кода сброса (без смены пароля)"""
    from email_service import verify_reset_code, store_reset_code, generate_reset_code
    
    # Получаем текущий код для проверки без удаления
    from email_service import reset_codes
    email_lower = data.email.lower()
    
    if email_lower not in reset_codes:
        raise HTTPException(status_code=400, detail="no_code_requested")
    
    stored = reset_codes[email_lower]
    
    from datetime import datetime, timezone
    if datetime.now(timezone.utc) > stored["expires_at"]:
        del reset_codes[email_lower]
        raise HTTPException(status_code=400, detail="code_expired")
    
    if stored["attempts"] >= 5:
        del reset_codes[email_lower]
        raise HTTPException(status_code=400, detail="too_many_attempts")
    
    if stored["code"] != data.code:
        stored["attempts"] += 1
        raise HTTPException(status_code=400, detail="invalid_code")
    
    # Код верный, но не удаляем его - пользователь еще будет менять пароль
    return {"status": "success", "valid": True}

@auth_router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Сброс пароля с использованием кода"""
    from server import db
    from email_service import verify_reset_code
    
    # Проверяем код
    success, message = verify_reset_code(data.email, data.code)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Проверяем длину нового пароля
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="password_too_short")
    
    # Обновляем пароль
    new_hash = pwd_context.hash(data.new_password)
    
    result = await db.users.update_one(
        {"email": data.email},
        {"$set": {"hashed_password": new_hash}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="user_not_found")
    
    return {"status": "success", "message": "password_changed"}
