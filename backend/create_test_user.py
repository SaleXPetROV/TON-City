import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
import uuid

# Load environment
from dotenv import load_dotenv
load_dotenv()

mongo_url = os.environ.get('MONGO_URL', 'mongodb://127.0.0.1:27017/toncity')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'toncity')]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    username = "test_player"
    wallet = "0:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    password = "password123"
    
    # Check if exists
    existing = await db.users.find_one({"username": username})
    if existing:
        print(f"User '{username}' already exists.")
        print(f"Wallet: {existing.get('wallet_address')}")
        # Update password just in case
        hashed = pwd_context.hash(password)
        await db.users.update_one(
            {"_id": existing["_id"]}, 
            {"$set": {"hashed_password": hashed, "wallet_address": wallet, "balance_ton": 1000.0}}
        )
        print("Updated password and set balance to 1000 TON.")
        return

    hashed = pwd_context.hash(password)
    
    new_user = {
        "id": str(uuid.uuid4()),
        "wallet_address": wallet,
        "raw_address": wallet,
        "username": username,
        "display_name": "Test Player",
        "email": "test@example.com",
        "hashed_password": hashed,
        "avatar": None,
        "language": "ru",
        "is_admin": True,
        "balance_ton": 1000.0,
        "level": 5,
        "xp": 5000,
        "total_turnover": 0,
        "total_income": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": datetime.now(timezone.utc).isoformat(),
        "plots_owned": [],
        "businesses_owned": []
    }
    
    result = await db.users.insert_one(new_user)
    print(f"User '{username}' created successfully!")
    print(f"ID: {result.inserted_id}")
    print(f"Wallet: {wallet}")
    print(f"Password: {password}")

if __name__ == "__main__":
    asyncio.run(create_test_user())
