#!/usr/bin/env python3
"""
TON City Builder - Full Simulation Script
- Clears database and creates 100 users
- Simulates 2 weeks of user activity
- Creates businesses at various levels (1-10)
- Executes trades, land sales, chat messages
- Provides test user credentials
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Connect to MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'TEST_1')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Business types and tiers
TIER1_BUSINESSES = ['helios', 'nano_dc', 'quartz_mine', 'signal', 'cooler', 'bio_farm', 'scrap']
TIER2_BUSINESSES = ['chip_fab', 'nft_studio', 'ai_lab', 'hangar', 'cafe', 'repair', 'vr_club']
TIER3_BUSINESSES = ['validator', 'gram_bank', 'dex', 'casino', 'arena', 'incubator', 'bridge']

# Resource types per business
BUSINESS_PRODUCES = {
    'helios': 'energy', 'nano_dc': 'cu', 'quartz_mine': 'quartz', 
    'signal': 'traffic', 'cooler': 'cooling', 'bio_farm': 'food', 'scrap': 'scrap',
    'chip_fab': 'chips', 'nft_studio': 'nft', 'ai_lab': 'algo',
    'hangar': 'logistics', 'repair': 'iron'
}

BUSINESS_COSTS = {
    'helios': 5, 'nano_dc': 8, 'quartz_mine': 6, 'signal': 4, 'cooler': 5, 'bio_farm': 4, 'scrap': 3,
    'chip_fab': 15, 'nft_studio': 20, 'ai_lab': 25, 'hangar': 12, 'cafe': 10, 'repair': 8, 'vr_club': 18,
    'validator': 50, 'gram_bank': 60, 'dex': 55, 'casino': 70, 'arena': 45, 'incubator': 40, 'bridge': 48
}

# Names for users
FIRST_NAMES = ['Alex', 'Max', 'Ivan', 'Dmitry', 'Sergey', 'Andrey', 'Nikita', 'Artem', 'Pavel', 'Roman',
               'Maria', 'Anna', 'Elena', 'Olga', 'Natalia', 'Victoria', 'Ekaterina', 'Anastasia', 'Julia', 'Daria',
               'CryptoKing', 'TONMaster', 'BlockWizard', 'DeFiPro', 'NFTHunter', 'ChainLord', 'HashPower', 'CoinBoss']

LAST_NAMES = ['_trader', '_investor', '_whale', '_hodler', '_builder', '_miner', '_validator', '_dev', 
              '_pro', '_king', '_master', '_chief', '_boss', '2024', '2025', '_ton', '_web3']

# Chat messages templates
GLOBAL_MESSAGES = [
    "Всем привет! Как дела на острове?",
    "Кто хочет обменяться ресурсами?",
    "Продаю энергию по выгодной цене!",
    "Ищу патрона для своего бизнеса",
    "Только что апгрейднул завод до 10 уровня! 🎉",
    "Кварц нужен срочно, плачу x2",
    "Кто-нибудь знает как ускорить производство?",
    "Мой валидатор приносит 5% в день",
    "Ищу партнера для совместного бизнеса",
    "Тут кто-то продает землю в центре?",
    "Казино окупилось за 3 дня!",
    "Какой бизнес лучше для новичка?",
    "Грам Банк - лучшая инвестиция",
    "Кто покупает NFT?",
    "DEX биржа - must have для трейдеров",
]

TRADE_MESSAGES = [
    "Интересное предложение, беру!",
    "Цена завышена, сбавь",
    "Договорились, переводи",
    "Отличная сделка! 👍",
    "Еще раз такую сделку сделаем?",
]


class SimulationRunner:
    def __init__(self):
        self.users = []
        self.plots = []
        self.businesses = []
        self.available_cells = []
        self.test_user = None
        
    async def clear_database(self):
        """Clear all game data"""
        print("🗑️  Очистка базы данных...")
        
        collections = ['users', 'plots', 'businesses', 'market_listings', 'transactions',
                      'land_listings', 'chat_messages', 'notifications', 'admin_stats']
        
        for col in collections:
            result = await db[col].delete_many({})
            print(f"   ✓ {col}: удалено {result.deleted_count} записей")
        
        # Reset island ownership
        await db.islands.update_one(
            {"id": "ton_island"},
            {"$set": {"cells.$[].owner": None, "cells.$[].business": None}}
        )
        
        print("   ✅ База данных очищена")
        
    async def get_available_cells(self):
        """Get list of available cells from island"""
        island = await db.islands.find_one({"id": "ton_island"}, {"_id": 0})
        if island:
            self.available_cells = [c for c in island.get("cells", []) if not c.get("owner")]
            random.shuffle(self.available_cells)
        print(f"   📍 Доступно {len(self.available_cells)} участков")
        
    async def create_users(self):
        """Create 100 users with varying balances"""
        print("\n👥 Создание 100 пользователей...")
        
        for i in range(100):
            # Generate balance: some rich, some middle, some starting
            if i < 10:  # Top 10 - whales (500-1000 TON)
                balance = random.uniform(500, 1000)
            elif i < 30:  # Next 20 - rich (200-500 TON)
                balance = random.uniform(200, 500)
            elif i < 60:  # Middle 30 (100-200 TON)
                balance = random.uniform(100, 200)
            else:  # Rest - starting (50-100 TON)
                balance = random.uniform(50, 100)
            
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            username = f"{first}{last}_{i+1}"
            
            user = {
                "id": str(uuid.uuid4()),
                "username": username,
                "display_name": username,
                "email": f"{username.lower()}@test.com",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.S3vZ1P9nX5VZke",  # Test123!
                "wallet_address": f"EQ{uuid.uuid4().hex[:46]}",
                "raw_address": None,
                "avatar": f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'><circle cx='50' cy='50' r='40' fill='%23{random.randint(0,0xffffff):06x}'/></svg>",
                "balance_ton": round(balance, 2),
                "language": random.choice(["ru", "en"]),
                "level": "novice",
                "xp": random.randint(0, 5000),
                "total_turnover": 0,
                "total_income": 0,
                "plots_owned": [],
                "businesses_owned": [],
                "is_admin": (i == 0),  # First user is admin
                "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(7, 30)),
                "last_login": datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 48)),
            }
            
            await db.users.insert_one(user)
            self.users.append(user)
            
            if i % 20 == 19:
                print(f"   ✓ Создано {i+1}/100 пользователей")
        
        # Select test user (rich one with businesses later)
        self.test_user = self.users[5]  # 6th user - one of the rich ones
        print(f"   ✅ Создано 100 пользователей")
        
    async def buy_plots_and_build(self):
        """Buy plots and build businesses"""
        print("\n🏗️  Покупка участков и строительство бизнесов...")
        
        cell_idx = 0
        total_plots = 0
        total_businesses = 0
        
        for i, user in enumerate(self.users):
            if cell_idx >= len(self.available_cells):
                break
            
            # Determine how many plots this user buys
            if i < 10:  # Whales get 5-8 plots
                num_plots = random.randint(5, 8)
            elif i < 30:  # Rich get 3-5 plots
                num_plots = random.randint(3, 5)
            elif i < 60:  # Middle get 1-3 plots
                num_plots = random.randint(1, 3)
            else:  # Others get 0-1 plots
                num_plots = random.randint(0, 1)
            
            user_plots = []
            user_businesses = []
            
            for _ in range(num_plots):
                if cell_idx >= len(self.available_cells):
                    break
                
                cell = self.available_cells[cell_idx]
                cell_idx += 1
                
                # Create plot
                plot = {
                    "id": str(uuid.uuid4()),
                    "island_id": "ton_island",
                    "x": cell["x"],
                    "y": cell["y"],
                    "zone": cell.get("zone", "outer"),
                    "price": cell.get("price", 1.0),
                    "owner": user["id"],
                    "owner_username": user["username"],
                    "business": None,
                    "warehouses": [],
                    "for_sale": False,
                    "sale_price": None,
                    "purchased_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 14))).isoformat()
                }
                
                await db.plots.insert_one(plot.copy())
                user_plots.append(plot)
                total_plots += 1
                
                # Build business (80% chance)
                if random.random() < 0.8:
                    # Choose business type based on user wealth
                    if i < 10 and random.random() < 0.5:  # Whales can have tier 3
                        biz_type = random.choice(TIER3_BUSINESSES)
                    elif i < 30 and random.random() < 0.4:  # Rich can have tier 2
                        biz_type = random.choice(TIER2_BUSINESSES)
                    else:
                        biz_type = random.choice(TIER1_BUSINESSES)
                    
                    # Level based on wealth and time
                    if i < 10:
                        level = random.randint(5, 10)
                    elif i < 30:
                        level = random.randint(3, 8)
                    elif i < 60:
                        level = random.randint(1, 5)
                    else:
                        level = random.randint(1, 3)
                    
                    # Determine tier
                    if biz_type in TIER1_BUSINESSES:
                        tier = 1
                    elif biz_type in TIER2_BUSINESSES:
                        tier = 2
                    else:
                        tier = 3
                    
                    business = {
                        "id": str(uuid.uuid4()),
                        "island_id": "ton_island",
                        "plot_id": plot["id"],
                        "x": cell["x"],
                        "y": cell["y"],
                        "business_type": biz_type,
                        "level": level,
                        "tier": tier,
                        "durability": round(random.uniform(50, 100), 1),
                        "xp": random.randint(0, level * 1000),
                        "owner": user["id"],
                        "owner_wallet": user.get("wallet_address"),
                        "owner_username": user["username"],
                        "patron": None,
                        "patron_id": None,
                        "storage": {
                            "capacity": 500 + level * 100,
                            "items": {BUSINESS_PRODUCES.get(biz_type, 'energy'): random.randint(10, 200)} if BUSINESS_PRODUCES.get(biz_type) else {}
                        },
                        "pending_income": round(random.uniform(0, level * 0.1), 4),
                        "last_collection": (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))).isoformat(),
                        "last_wear_update": datetime.now(timezone.utc).isoformat(),
                        "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 14))).isoformat()
                    }
                    
                    await db.businesses.insert_one(business.copy())
                    user_businesses.append(business)
                    total_businesses += 1
                    
                    # Update plot with business
                    await db.plots.update_one(
                        {"id": plot["id"]},
                        {"$set": {"business": biz_type}}
                    )
            
            # Update user with plots and businesses
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {
                    "plots_owned": [p["id"] for p in user_plots],
                    "businesses_owned": [b["id"] for b in user_businesses]
                }}
            )
            
            if (i + 1) % 20 == 0:
                print(f"   ✓ Обработано {i+1}/100 пользователей")
        
        print(f"   ✅ Куплено {total_plots} участков, построено {total_businesses} бизнесов")
        
    async def create_market_listings(self):
        """Create market listings for resources"""
        print("\n📊 Создание предложений на рынке...")
        
        businesses = await db.businesses.find({}, {"_id": 0}).to_list(1000)
        listings_created = 0
        
        for biz in businesses:
            # 30% chance to list resources
            if random.random() < 0.3:
                resource = BUSINESS_PRODUCES.get(biz["business_type"])
                if not resource:
                    continue
                
                amount = random.uniform(20, 200)
                price = random.uniform(0.002, 0.02)
                
                listing = {
                    "id": str(uuid.uuid4()),
                    "seller_id": biz["owner"],
                    "seller_email": f"{biz['owner_username'].lower()}@test.com",
                    "seller_username": biz["owner_username"],
                    "business_id": biz["id"],
                    "resource_type": resource,
                    "amount": round(amount, 2),
                    "price_per_unit": round(price, 6),
                    "total_price": round(amount * price, 4),
                    "status": "active",
                    "created_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))).isoformat()
                }
                
                await db.market_listings.insert_one(listing.copy())
                listings_created += 1
        
        print(f"   ✅ Создано {listings_created} предложений на рынке")
        
    async def create_land_listings(self):
        """Create land sales (with and without businesses)"""
        print("\n🏠 Создание предложений продажи земли...")
        
        plots = await db.plots.find({}, {"_id": 0}).to_list(1000)
        land_listings = 0
        
        for plot in plots:
            # 10% chance to list for sale
            if random.random() < 0.1:
                base_price = plot.get("price", 1.0)
                # Premium for location and business
                multiplier = random.uniform(1.2, 3.0)
                if plot.get("business"):
                    multiplier *= 1.5  # 50% more for plots with business
                
                sale_price = round(base_price * multiplier, 2)
                
                await db.plots.update_one(
                    {"id": plot["id"]},
                    {"$set": {"for_sale": True, "sale_price": sale_price}}
                )
                
                # Create land listing
                listing = {
                    "id": str(uuid.uuid4()),
                    "plot_id": plot["id"],
                    "seller_id": plot["owner"],
                    "seller_username": plot["owner_username"],
                    "x": plot["x"],
                    "y": plot["y"],
                    "zone": plot.get("zone", "outer"),
                    "has_business": plot.get("business") is not None,
                    "business_type": plot.get("business"),
                    "price": sale_price,
                    "status": "active",
                    "created_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))).isoformat()
                }
                
                await db.land_listings.insert_one(listing.copy())
                land_listings += 1
        
        print(f"   ✅ Создано {land_listings} предложений продажи земли")
        
    async def simulate_trades(self):
        """Simulate trades between users"""
        print("\n💰 Симуляция торговых сделок...")
        
        listings = await db.market_listings.find({"status": "active"}, {"_id": 0}).to_list(100)
        trades = 0
        total_volume = 0
        total_tax = 0
        
        for listing in listings:
            # 50% chance each listing gets bought
            if random.random() < 0.5:
                # Find a buyer (not the seller)
                buyers = [u for u in self.users if u["id"] != listing["seller_id"]]
                if not buyers:
                    continue
                
                buyer = random.choice(buyers)
                amount = min(listing["amount"], random.uniform(5, 50))
                total_cost = amount * listing["price_per_unit"]
                
                if buyer["balance_ton"] < total_cost:
                    continue
                
                # Calculate tax (13%)
                tax = total_cost * 0.13
                seller_receives = total_cost - tax
                
                # Update balances
                await db.users.update_one(
                    {"id": buyer["id"]},
                    {"$inc": {"balance_ton": -total_cost, "total_turnover": total_cost}}
                )
                
                await db.users.update_one(
                    {"id": listing["seller_id"]},
                    {"$inc": {"balance_ton": seller_receives, "total_income": seller_receives}}
                )
                
                # Update listing
                new_amount = listing["amount"] - amount
                if new_amount <= 0:
                    await db.market_listings.update_one(
                        {"id": listing["id"]},
                        {"$set": {"status": "sold"}}
                    )
                else:
                    await db.market_listings.update_one(
                        {"id": listing["id"]},
                        {"$set": {"amount": new_amount}}
                    )
                
                # Record transaction
                tx = {
                    "id": str(uuid.uuid4()),
                    "type": "market_trade",
                    "buyer_id": buyer["id"],
                    "seller_id": listing["seller_id"],
                    "resource_type": listing["resource_type"],
                    "amount": round(amount, 2),
                    "price_per_unit": listing["price_per_unit"],
                    "total_cost": round(total_cost, 4),
                    "tax": round(tax, 4),
                    "seller_received": round(seller_receives, 4),
                    "created_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 336))).isoformat()
                }
                
                await db.transactions.insert_one(tx.copy())
                
                trades += 1
                total_volume += total_cost
                total_tax += tax
        
        # Update treasury
        await db.admin_stats.update_one(
            {"type": "treasury"},
            {"$inc": {"market_tax": total_tax, "total_tax": total_tax}},
            upsert=True
        )
        
        print(f"   ✅ Выполнено {trades} сделок, объём: {total_volume:.2f} TON, налоги: {total_tax:.2f} TON")
        
    async def create_chat_messages(self):
        """Create global and city chat messages"""
        print("\n💬 Создание сообщений в чате...")
        
        messages_created = 0
        
        # Global chat messages
        for _ in range(50):
            user = random.choice(self.users)
            msg = {
                "id": str(uuid.uuid4()),
                "channel": "global",
                "user_id": user["id"],
                "username": user["username"],
                "avatar": user.get("avatar"),
                "text": random.choice(GLOBAL_MESSAGES),
                "created_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 168))).isoformat()
            }
            await db.chat_messages.insert_one(msg.copy())
            messages_created += 1
        
        # Trade channel messages
        for _ in range(30):
            user = random.choice(self.users)
            msg = {
                "id": str(uuid.uuid4()),
                "channel": "trade",
                "user_id": user["id"],
                "username": user["username"],
                "avatar": user.get("avatar"),
                "text": random.choice(TRADE_MESSAGES + GLOBAL_MESSAGES[:5]),
                "created_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 72))).isoformat()
            }
            await db.chat_messages.insert_one(msg.copy())
            messages_created += 1
        
        # City chat (by zones)
        zones = ["core", "inner", "middle", "outer"]
        for zone in zones:
            for _ in range(10):
                user = random.choice(self.users)
                msg = {
                    "id": str(uuid.uuid4()),
                    "channel": f"zone_{zone}",
                    "user_id": user["id"],
                    "username": user["username"],
                    "avatar": user.get("avatar"),
                    "text": f"Привет соседям из зоны {zone}! " + random.choice(GLOBAL_MESSAGES[:5]),
                    "created_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 48))).isoformat()
                }
                await db.chat_messages.insert_one(msg.copy())
                messages_created += 1
        
        print(f"   ✅ Создано {messages_created} сообщений в чате")
        
    async def ensure_test_user_has_businesses(self):
        """Make sure test user has multiple businesses at different levels"""
        print("\n🔧 Настройка тестового пользователя...")
        
        # Get test user's businesses
        test_businesses = await db.businesses.find({"owner": self.test_user["id"]}, {"_id": 0}).to_list(100)
        
        # If not enough, create more
        if len(test_businesses) < 3:
            # Find plots without business owned by test user
            test_plots = await db.plots.find({"owner": self.test_user["id"], "business": None}, {"_id": 0}).to_list(10)
            
            # If no empty plots, buy more
            if len(test_plots) < 3 - len(test_businesses):
                for i in range(3 - len(test_businesses) - len(test_plots)):
                    if self.available_cells:
                        cell = self.available_cells.pop()
                        plot = {
                            "id": str(uuid.uuid4()),
                            "island_id": "ton_island",
                            "x": cell["x"],
                            "y": cell["y"],
                            "zone": cell.get("zone", "outer"),
                            "price": cell.get("price", 1.0),
                            "owner": self.test_user["id"],
                            "owner_username": self.test_user["username"],
                            "business": None,
                            "warehouses": [],
                            "for_sale": False,
                            "purchased_at": datetime.now(timezone.utc).isoformat()
                        }
                        await db.plots.insert_one(plot.copy())
                        test_plots.append(plot)
            
            # Build businesses on empty plots
            biz_types = ['helios', 'chip_fab', 'validator']  # One from each tier
            levels = [3, 6, 9]  # Different levels to test sprites
            
            for i, plot in enumerate(test_plots[:3]):
                biz_type = biz_types[i % 3]
                level = levels[i % 3]
                
                if biz_type in TIER1_BUSINESSES:
                    tier = 1
                elif biz_type in TIER2_BUSINESSES:
                    tier = 2
                else:
                    tier = 3
                
                business = {
                    "id": str(uuid.uuid4()),
                    "island_id": "ton_island",
                    "plot_id": plot["id"],
                    "x": plot["x"],
                    "y": plot["y"],
                    "business_type": biz_type,
                    "level": level,
                    "tier": tier,
                    "durability": 85.0,
                    "xp": level * 500,
                    "owner": self.test_user["id"],
                    "owner_wallet": self.test_user.get("wallet_address"),
                    "owner_username": self.test_user["username"],
                    "patron": None,
                    "storage": {"capacity": 500 + level * 100, "items": {}},
                    "pending_income": 0.05,
                    "last_collection": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.businesses.insert_one(business.copy())
                await db.plots.update_one({"id": plot["id"]}, {"$set": {"business": biz_type}})
        
        # Update test user level based on XP
        await db.users.update_one(
            {"id": self.test_user["id"]},
            {"$set": {"level": "expert", "xp": 15000}}
        )
        
        # Get updated test user
        self.test_user = await db.users.find_one({"id": self.test_user["id"]}, {"_id": 0})
        test_businesses = await db.businesses.find({"owner": self.test_user["id"]}, {"_id": 0}).to_list(100)
        
        print(f"   ✅ Тестовый пользователь: {self.test_user['username']}")
        print(f"      Email: {self.test_user['email']}")
        print(f"      Баланс: {self.test_user['balance_ton']:.2f} TON")
        print(f"      Бизнесов: {len(test_businesses)}")
        for biz in test_businesses:
            print(f"         - {biz['business_type']} (уровень {biz['level']})")
        
    async def print_summary(self):
        """Print simulation summary"""
        print("\n" + "="*60)
        print("📊 ИТОГИ СИМУЛЯЦИИ")
        print("="*60)
        
        users_count = await db.users.count_documents({})
        plots_count = await db.plots.count_documents({})
        businesses_count = await db.businesses.count_documents({})
        listings_count = await db.market_listings.count_documents({"status": "active"})
        land_listings_count = await db.land_listings.count_documents({"status": "active"})
        messages_count = await db.chat_messages.count_documents({})
        trades_count = await db.transactions.count_documents({})
        
        treasury = await db.admin_stats.find_one({"type": "treasury"}, {"_id": 0})
        
        print(f"   👥 Пользователей: {users_count}")
        print(f"   🏠 Участков: {plots_count}")
        print(f"   🏭 Бизнесов: {businesses_count}")
        print(f"   📊 Активных листингов: {listings_count}")
        print(f"   🏷️  Земля на продажу: {land_listings_count}")
        print(f"   💬 Сообщений в чате: {messages_count}")
        print(f"   💰 Торговых сделок: {trades_count}")
        print(f"   🏛️  Казна (налоги): {treasury.get('total_tax', 0):.2f} TON" if treasury else "   🏛️  Казна: 0 TON")
        
        # Business level distribution
        levels = await db.businesses.aggregate([
            {"$group": {"_id": "$level", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]).to_list(100)
        
        print("\n   📈 Распределение бизнесов по уровням:")
        for lvl in levels:
            print(f"      Уровень {lvl['_id']}: {lvl['count']} бизнесов")
        
        print("\n" + "="*60)
        print("🔑 ДАННЫЕ ДЛЯ ТЕСТИРОВАНИЯ")
        print("="*60)
        print(f"   📧 Email: {self.test_user['email']}")
        print(f"   🔐 Пароль: Test123!")
        print(f"   💰 Баланс: {self.test_user['balance_ton']:.2f} TON")
        print("="*60)
        
    async def run(self):
        """Run full simulation"""
        print("🚀 Запуск полной симуляции TON City Builder")
        print("="*60)
        
        await self.clear_database()
        await self.get_available_cells()
        await self.create_users()
        await self.buy_plots_and_build()
        await self.create_market_listings()
        await self.create_land_listings()
        await self.simulate_trades()
        await self.create_chat_messages()
        await self.ensure_test_user_has_businesses()
        await self.print_summary()


async def main():
    runner = SimulationRunner()
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
