"""
Create Test Users Script
Creates 3 test users: 1 admin and 2 regular users
"""
import asyncio
import uuid
import hashlib
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test user data
TEST_USERS = [
    {
        "username": "admin_ton",
        "email": "admin@toncity.io",
        "password": "Admin123!",
        "is_admin": True,
        "balance_ton": 1000.0,
        "level": 10,
        "display_name": "TON City Admin"
    },
    {
        "username": "player_one",
        "email": "player1@toncity.io",
        "password": "Player1!",
        "is_admin": False,
        "balance_ton": 100.0,
        "level": 3,
        "display_name": "Player One"
    },
    {
        "username": "player_two", 
        "email": "player2@toncity.io",
        "password": "Player2!",
        "is_admin": False,
        "balance_ton": 50.0,
        "level": 1,
        "display_name": "Player Two"
    }
]


def generate_avatar(username: str) -> str:
    """Generate simple SVG avatar from initials"""
    initials = username[:2].upper()
    
    # Generate color based on username hash
    hash_val = int(hashlib.md5(username.encode()).hexdigest()[:6], 16)
    hue = hash_val % 360
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <defs>
            <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:hsl({hue},70%,50%);stop-opacity:1" />
                <stop offset="100%" style="stop-color:hsl({(hue + 30) % 360},70%,40%);stop-opacity:1" />
            </linearGradient>
        </defs>
        <circle cx="50" cy="50" r="50" fill="url(#grad)"/>
        <text x="50" y="55" font-family="Arial, sans-serif" font-size="32" font-weight="bold" 
              fill="white" text-anchor="middle" dominant-baseline="middle">{initials}</text>
    </svg>'''
    
    import base64
    svg_bytes = svg.encode('utf-8')
    b64 = base64.b64encode(svg_bytes).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"


async def create_test_users():
    """Create test users in MongoDB"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'ton_city')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    created_users = []
    
    for user_data in TEST_USERS:
        # Check if user already exists
        existing = await db.users.find_one({
            "$or": [
                {"username": user_data["username"]},
                {"email": user_data["email"]}
            ]
        })
        
        if existing:
            print(f"User {user_data['username']} already exists, updating...")
            # Update existing user
            await db.users.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "hashed_password": pwd_context.hash(user_data["password"]),
                    "is_admin": user_data["is_admin"],
                    "balance_ton": user_data["balance_ton"],
                    "level": user_data["level"]
                }}
            )
            created_users.append({
                "id": existing.get("id"),
                "username": user_data["username"],
                "email": user_data["email"],
                "password": user_data["password"],
                "is_admin": user_data["is_admin"]
            })
            continue
        
        # Create new user
        user_doc = {
            "id": str(uuid.uuid4()),
            "username": user_data["username"],
            "email": user_data["email"],
            "hashed_password": pwd_context.hash(user_data["password"]),
            "display_name": user_data["display_name"],
            "avatar": generate_avatar(user_data["username"]),
            "is_admin": user_data["is_admin"],
            "balance_ton": user_data["balance_ton"],
            "level": user_data["level"],
            "xp": 0,
            "total_turnover": 0,
            "total_income": 0.0,
            "language": "ru",
            "is_2fa_enabled": False,
            "two_factor_secret": None,
            "backup_codes": [],
            "withdraw_lock_until": None,
            "plots_owned": [],
            "businesses_owned": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(user_doc)
        
        created_users.append({
            "id": user_doc["id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"],
            "is_admin": user_data["is_admin"]
        })
        
        print(f"Created user: {user_data['username']}")
    
    client.close()
    
    return created_users


async def main():
    print("\n" + "="*60)
    print("Creating test users for TON-City")
    print("="*60 + "\n")
    
    users = await create_test_users()
    
    print("\n" + "="*60)
    print("TEST USER CREDENTIALS")
    print("="*60)
    
    for user in users:
        admin_badge = " [ADMIN]" if user["is_admin"] else ""
        print(f"\n{user['username']}{admin_badge}")
        print(f"  Email: {user['email']}")
        print(f"  Password: {user['password']}")
    
    print("\n" + "="*60)
    print("Users created successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
