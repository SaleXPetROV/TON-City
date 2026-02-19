"""
Simulation script: Create 100 test users with 2+ weeks of gameplay history
This includes:
- Plot purchases
- Business builds and upgrades
- Resource production
- Trading between users
- Deposits and withdrawals
- Commission earnings
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'TEST_1')]

# Business types by tier
TIER1_BUSINESSES = ['helios', 'nano_dc', 'quartz_mine', 'signal', 'cooler', 'bio_farm', 'scrap']
TIER2_BUSINESSES = ['chip_fab', 'nft_studio', 'ai_lab', 'hangar', 'cafe', 'repair', 'vr_club']
TIER3_BUSINESSES = ['validator', 'gram_bank', 'dex', 'casino', 'arena', 'incubator', 'bridge']

# Prices per zone
ZONE_PRICES = {
    'core': 3.0,
    'inner': 2.0,
    'middle': 1.5,
    'outer': 1.0
}

# Usernames for test accounts
USERNAMES = [
    "CryptoKing", "TONMaster", "BlockchainPro", "DeFiHunter", "NFTCollector",
    "IslandBuilder", "CityTycoon", "TechGuru", "DigitalNomad", "MetaTrader",
    "ChainExplorer", "TokenHolder", "StakeKing", "MiningBoss", "TradeWizard",
    "CryptoWhale", "DappDev", "Web3Pioneer", "SmartContract", "GasOptimizer",
    "YieldFarmer", "LiquidityPro", "SwapMaster", "BridgeRunner", "OracleNode",
    "ValidatorX", "ConsensusKing", "ShardMaster", "L2Builder", "RollupDev",
    "ZKProof", "PrivacyChain", "AnonTrader", "SecureWallet", "ColdStorage",
    "HotWallet", "MultiSig", "DaoMember", "GovernanceVote", "ProposalMaker",
    "AirdropHunter", "ICOVeteran", "IDOExpert", "LaunchpadPro", "SeedInvestor",
    "AngelsClub", "VCFund", "CapitalFlow", "AssetManager", "PortfolioX"
]

async def clear_existing_data():
    """Clear existing test data"""
    print("🗑️ Clearing existing test data...")
    
    # Keep real users (those with real wallet addresses)
    # Delete only simulated users (test_ prefix)
    await db.users.delete_many({"username": {"$regex": "^Test_"}})
    await db.transactions.delete_many({"description": {"$regex": "Симуляция"}})
    
    print("✅ Test data cleared")

async def generate_test_users(count=100):
    """Generate test users with varied profiles"""
    print(f"\n👥 Creating {count} test users...")
    
    users = []
    start_date = datetime.utcnow() - timedelta(days=16)  # Started 16 days ago
    
    for i in range(count):
        username = f"Test_{USERNAMES[i % len(USERNAMES)]}_{i+1}"
        
        # Random registration date (1-16 days ago)
        days_ago = random.randint(1, 16)
        created_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        # Initial deposit between 10-200 TON
        initial_balance = round(random.uniform(10, 200), 2)
        
        # Activity level affects earnings
        activity_level = random.choice(['casual', 'regular', 'active', 'whale'])
        activity_multipliers = {
            'casual': 0.5,
            'regular': 1.0,
            'active': 1.5,
            'whale': 3.0
        }
        
        # Calculate total earnings over time
        days_playing = days_ago
        daily_income_base = initial_balance * 0.02  # 2% daily base income
        total_income = daily_income_base * days_playing * activity_multipliers[activity_level]
        
        # Current balance = initial + earnings - spending (random)
        spending = total_income * random.uniform(0.3, 0.7)
        current_balance = round(initial_balance + total_income - spending, 2)
        current_balance = max(1.0, current_balance)  # Minimum 1 TON
        
        # Generate fake wallet address
        wallet_raw = f"0:{uuid.uuid4().hex}"
        wallet_display = f"EQ{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=46))}"
        
        user = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": f"{username.lower()}@test.local",
            "wallet_address": wallet_raw,
            "wallet_address_raw": wallet_raw,
            "wallet_address_display": wallet_display,
            "balance_ton": current_balance,
            "total_earned": round(total_income, 2),
            "total_spent": round(spending, 2),
            "is_admin": False,
            "is_active": True,
            "created_at": created_at,
            "last_active": datetime.utcnow() - timedelta(hours=random.randint(0, 48)),
            "activity_level": activity_level,
            "reputation_score": random.randint(0, 100),
            "achievements": [],
            "auth_provider": "simulation"
        }
        users.append(user)
    
    # Insert users
    if users:
        await db.users.insert_many(users)
    
    print(f"✅ Created {len(users)} users")
    return users

async def assign_plots_to_users(users):
    """Assign random plots to users"""
    print("\n🏠 Assigning plots to users...")
    
    # Get all available plots
    island = await db.islands.find_one({"id": "ton_island"})
    if not island or 'cells' not in island:
        print("❌ Island not found!")
        return
    
    cells = island.get('cells', [])
    available_cells = [c for c in cells if not c.get('owner')]
    
    total_assigned = 0
    
    for user in users:
        # Number of plots based on activity level
        plots_count = {
            'casual': random.randint(1, 3),
            'regular': random.randint(2, 5),
            'active': random.randint(4, 8),
            'whale': random.randint(6, 15)
        }.get(user['activity_level'], 2)
        
        plots_count = min(plots_count, len(available_cells))
        
        for _ in range(plots_count):
            if not available_cells:
                break
            
            # Pick random cell
            idx = random.randint(0, len(available_cells) - 1)
            cell = available_cells.pop(idx)
            
            # Assign to user
            cell['owner'] = user['id']
            cell['owner_username'] = user['username']
            cell['purchased_at'] = user['created_at'] + timedelta(hours=random.randint(1, 72))
            cell['is_available'] = False
            total_assigned += 1
    
    # Update island with assigned plots
    await db.islands.update_one(
        {"id": "ton_island"},
        {"$set": {"cells": cells}}
    )
    
    print(f"✅ Assigned {total_assigned} plots to users")
    return cells

async def build_businesses(users, cells):
    """Build businesses on owned plots"""
    print("\n🏗️ Building businesses...")
    
    businesses_built = 0
    
    for cell in cells:
        if not cell.get('owner'):
            continue
        
        # 70% chance to build on owned plot
        if random.random() > 0.7:
            continue
        
        user = next((u for u in users if u['id'] == cell['owner']), None)
        if not user:
            continue
        
        # Choose business tier based on zone
        zone = cell.get('zone', 'outer')
        
        if zone == 'core':
            business_types = TIER3_BUSINESSES
            max_level = random.randint(3, 10)
        elif zone == 'inner':
            business_types = TIER2_BUSINESSES + TIER3_BUSINESSES
            max_level = random.randint(2, 8)
        elif zone == 'middle':
            business_types = TIER1_BUSINESSES + TIER2_BUSINESSES
            max_level = random.randint(1, 6)
        else:  # outer
            business_types = TIER1_BUSINESSES
            max_level = random.randint(1, 4)
        
        # Random business type from available
        business_type = random.choice(business_types)
        
        # Random level (higher activity = higher levels)
        level_boost = {'casual': 0, 'regular': 1, 'active': 2, 'whale': 3}.get(user['activity_level'], 0)
        level = min(random.randint(1, max_level) + level_boost, 10)
        
        # Determine tier
        if business_type in TIER1_BUSINESSES:
            tier = 1
        elif business_type in TIER2_BUSINESSES:
            tier = 2
        else:
            tier = 3
        
        # Add business to cell
        cell['business'] = {
            'type': business_type,
            'level': level,
            'tier': tier,
            'built_at': cell['purchased_at'] + timedelta(hours=random.randint(1, 24)),
            'last_collection': datetime.utcnow() - timedelta(hours=random.randint(1, 12)),
            'total_collected': round(random.uniform(0.5, 50) * level, 2),
            'health': random.randint(70, 100),
            'is_active': True
        }
        
        businesses_built += 1
    
    # Update island
    await db.islands.update_one(
        {"id": "ton_island"},
        {"$set": {"cells": cells}}
    )
    
    print(f"✅ Built {businesses_built} businesses")

async def generate_transactions(users):
    """Generate transaction history for users"""
    print("\n💰 Generating transaction history...")
    
    transactions = []
    
    for user in users:
        days_active = (datetime.utcnow() - user['created_at']).days
        
        # Initial deposit
        transactions.append({
            "id": str(uuid.uuid4()),
            "user_id": user['id'],
            "type": "deposit",
            "amount": round(random.uniform(10, 100), 2),
            "description": "Симуляция: Первичный депозит",
            "status": "completed",
            "created_at": user['created_at'] + timedelta(minutes=5),
            "completed_at": user['created_at'] + timedelta(minutes=10)
        })
        
        # Daily transactions
        for day in range(days_active):
            date = user['created_at'] + timedelta(days=day)
            
            # Income collection (1-3 per day)
            for _ in range(random.randint(1, 3)):
                amount = round(random.uniform(0.01, 2.0), 4)
                transactions.append({
                    "id": str(uuid.uuid4()),
                    "user_id": user['id'],
                    "type": "income",
                    "amount": amount,
                    "description": "Симуляция: Доход от бизнеса",
                    "status": "completed",
                    "created_at": date + timedelta(hours=random.randint(0, 23)),
                    "completed_at": date + timedelta(hours=random.randint(0, 23))
                })
            
            # Random trades (0-2 per day)
            for _ in range(random.randint(0, 2)):
                other_user = random.choice([u for u in users if u['id'] != user['id']])
                amount = round(random.uniform(0.5, 10), 2)
                
                # Buyer transaction
                transactions.append({
                    "id": str(uuid.uuid4()),
                    "user_id": user['id'],
                    "type": "trade_buy" if random.random() > 0.5 else "trade_sell",
                    "amount": amount,
                    "counterparty_id": other_user['id'],
                    "description": f"Симуляция: Торговля с {other_user['username']}",
                    "status": "completed",
                    "created_at": date + timedelta(hours=random.randint(0, 23)),
                    "completed_at": date + timedelta(hours=random.randint(0, 23))
                })
        
        # Occasional withdrawals (whale users)
        if user['activity_level'] == 'whale' and random.random() > 0.7:
            transactions.append({
                "id": str(uuid.uuid4()),
                "user_id": user['id'],
                "type": "withdrawal",
                "amount": round(random.uniform(5, 30), 2),
                "description": "Симуляция: Вывод средств",
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 5)),
                "completed_at": datetime.utcnow() - timedelta(days=random.randint(1, 5))
            })
    
    # Insert transactions
    if transactions:
        await db.transactions.insert_many(transactions)
    
    print(f"✅ Generated {len(transactions)} transactions")

async def generate_leaderboard_data(users):
    """Generate leaderboard entries"""
    print("\n🏆 Generating leaderboard data...")
    
    # Sort users by earnings
    sorted_users = sorted(users, key=lambda u: u.get('total_earned', 0), reverse=True)
    
    leaderboard = []
    for rank, user in enumerate(sorted_users[:50], 1):
        leaderboard.append({
            "user_id": user['id'],
            "username": user['username'],
            "rank": rank,
            "total_earned": user.get('total_earned', 0),
            "businesses_count": random.randint(1, 10),
            "plots_count": random.randint(1, 15),
            "updated_at": datetime.utcnow()
        })
    
    # Clear and insert
    await db.leaderboard.delete_many({})
    if leaderboard:
        await db.leaderboard.insert_many(leaderboard)
    
    print(f"✅ Generated leaderboard with {len(leaderboard)} entries")

async def print_test_credentials():
    """Print credentials for a test account"""
    print("\n" + "=" * 60)
    print("📋 TEST ACCOUNT CREDENTIALS")
    print("=" * 60)
    
    # Get a whale user for best demonstration
    whale_user = await db.users.find_one({"activity_level": "whale", "username": {"$regex": "^Test_"}})
    
    if whale_user:
        print(f"\n🐋 Whale Account (for testing):")
        print(f"   Username: {whale_user['username']}")
        print(f"   Email: {whale_user['email']}")
        print(f"   Balance: {whale_user['balance_ton']:.2f} TON")
        print(f"   Total Earned: {whale_user.get('total_earned', 0):.2f} TON")
        print(f"   Wallet (raw): {whale_user['wallet_address'][:20]}...")
        print(f"   Activity: {whale_user['activity_level']}")
        print(f"   User ID: {whale_user['id']}")
    
    # Get statistics
    total_users = await db.users.count_documents({"username": {"$regex": "^Test_"}})
    total_transactions = await db.transactions.count_documents({"description": {"$regex": "Симуляция"}})
    
    # Count plots with owners
    island = await db.islands.find_one({"id": "ton_island"})
    owned_plots = sum(1 for c in island.get('cells', []) if c.get('owner'))
    plots_with_business = sum(1 for c in island.get('cells', []) if c.get('business'))
    
    print(f"\n📊 SIMULATION STATISTICS:")
    print(f"   Total Test Users: {total_users}")
    print(f"   Total Transactions: {total_transactions}")
    print(f"   Owned Plots: {owned_plots}")
    print(f"   Plots with Businesses: {plots_with_business}")
    print("=" * 60)

async def main():
    print("=" * 60)
    print("🎮 TON City Builder - 100 Users Simulation")
    print("=" * 60)
    
    # Clear existing test data
    await clear_existing_data()
    
    # Generate users
    users = await generate_test_users(100)
    
    # Assign plots
    cells = await assign_plots_to_users(users)
    
    # Build businesses
    await build_businesses(users, cells)
    
    # Generate transactions
    await generate_transactions(users)
    
    # Generate leaderboard
    await generate_leaderboard_data(users)
    
    # Print test credentials
    await print_test_credentials()
    
    print("\n✅ Simulation complete!")

if __name__ == "__main__":
    asyncio.run(main())
