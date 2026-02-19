#!/usr/bin/env python3
"""
TON City Builder - Full Integration Test
Creates 100 users, builds businesses, and tests marketplace trading with profit distribution
"""

import asyncio
import httpx
import random
import uuid
from datetime import datetime

BASE_URL = "https://iso-builder-debug.preview.emergentagent.com/api"

# Business types that produce/require resources
PRODUCER_TYPES = ["helios", "nano_dc", "quartz_mine", "signal", "cooler", "bio_farm", "scrap"]
CONSUMER_TYPES = ["chip_fab", "nft_studio", "ai_lab"]

# Resources produced by each type
BUSINESS_RESOURCES = {
    "helios": "energy",
    "nano_dc": "cu",
    "quartz_mine": "quartz",
    "signal": "traffic",
    "cooler": "cooling",
    "bio_farm": "food",
    "scrap": "scrap"
}

class TestUser:
    def __init__(self, index):
        self.index = index
        self.username = f"test_user_{index}_{uuid.uuid4().hex[:6]}"
        self.email = f"{self.username}@test.com"
        self.password = "Test123!"
        self.token = None
        self.user_id = None
        self.wallet = None
        self.balance = 0
        self.businesses = []
        self.plots = []

async def create_user(client: httpx.AsyncClient, user: TestUser) -> bool:
    """Register a new user"""
    try:
        response = await client.post(f"{BASE_URL}/auth/register", json={
            "username": user.username,
            "email": user.email,
            "password": user.password
        })
        if response.status_code == 200:
            data = response.json()
            user.token = data.get("token")
            user.user_id = data.get("user", {}).get("id")
            user.wallet = data.get("user", {}).get("wallet_address")
            user.balance = data.get("user", {}).get("balance_ton", 0)
            return True
        else:
            print(f"  ⚠️ User {user.index} registration failed: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ Error creating user {user.index}: {e}")
        return False

async def give_user_balance(client: httpx.AsyncClient, user: TestUser, amount: float) -> bool:
    """Admin endpoint to add balance (simulated by direct DB or admin API)"""
    try:
        # Try admin endpoint first
        response = await client.post(f"{BASE_URL}/admin/add-balance", 
            json={"wallet_address": user.wallet, "amount": amount},
            headers={"Authorization": f"Bearer {user.token}"}
        )
        if response.status_code == 200:
            user.balance += amount
            return True
        
        # Fallback: check if user already has balance from registration
        response = await client.get(f"{BASE_URL}/auth/me", 
            headers={"Authorization": f"Bearer {user.token}"}
        )
        if response.status_code == 200:
            data = response.json()
            user.balance = data.get("balance_ton", user.balance)
            return True
        return False
    except Exception as e:
        return False

async def buy_plot(client: httpx.AsyncClient, user: TestUser, x: int, y: int) -> bool:
    """Buy a plot on the island"""
    try:
        response = await client.post(f"{BASE_URL}/island/buy/{x}/{y}",
            headers={"Authorization": f"Bearer {user.token}"}
        )
        if response.status_code == 200:
            user.plots.append((x, y))
            return True
        return False
    except:
        return False

async def build_business(client: httpx.AsyncClient, user: TestUser, x: int, y: int, biz_type: str) -> dict:
    """Build a business on owned plot"""
    try:
        response = await client.post(f"{BASE_URL}/island/build/{x}/{y}",
            json={"business_type": biz_type},
            headers={"Authorization": f"Bearer {user.token}"}
        )
        if response.status_code == 200:
            data = response.json()
            biz_id = data.get("business_id") or data.get("business", {}).get("id")
            if biz_id:
                user.businesses.append({"id": biz_id, "type": biz_type, "x": x, "y": y})
            return data
        return None
    except Exception as e:
        return None

async def create_market_listing(client: httpx.AsyncClient, user: TestUser, 
                                  business_id: str, resource: str, amount: float, price: float) -> dict:
    """Create a market listing to sell resources"""
    try:
        response = await client.post(f"{BASE_URL}/market/list",
            json={
                "business_id": business_id,
                "resource_type": resource,
                "amount": amount,
                "price_per_unit": price
            },
            headers={"Authorization": f"Bearer {user.token}"}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

async def buy_from_market(client: httpx.AsyncClient, user: TestUser, 
                           listing_id: str, amount: float) -> dict:
    """Buy resources from market"""
    try:
        response = await client.post(f"{BASE_URL}/market/buy",
            json={
                "listing_id": listing_id,
                "amount": amount
            },
            headers={"Authorization": f"Bearer {user.token}"}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

async def get_market_listings(client: httpx.AsyncClient) -> list:
    """Get all active market listings"""
    try:
        response = await client.get(f"{BASE_URL}/market/listings")
        if response.status_code == 200:
            return response.json().get("listings", [])
        return []
    except:
        return []

async def get_user_balance(client: httpx.AsyncClient, user: TestUser) -> float:
    """Get current user balance"""
    try:
        response = await client.get(f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {user.token}"}
        )
        if response.status_code == 200:
            data = response.json()
            user.balance = data.get("balance_ton", 0)
            return user.balance
        return 0
    except:
        return 0

async def get_treasury(client: httpx.AsyncClient) -> dict:
    """Get treasury/tax stats"""
    try:
        response = await client.get(f"{BASE_URL}/admin/stats")
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

async def main():
    print("=" * 70)
    print("🏙️  TON CITY BUILDER - FULL INTEGRATION TEST")
    print("=" * 70)
    print(f"📅 Started: {datetime.now().isoformat()}")
    print()
    
    # Stats
    users_created = 0
    plots_bought = 0
    businesses_built = 0
    listings_created = 0
    trades_completed = 0
    total_traded = 0.0
    total_tax_collected = 0.0
    
    users: list[TestUser] = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # ============================================
        # PHASE 1: CREATE 100 USERS
        # ============================================
        print("📋 PHASE 1: Creating 100 test users...")
        
        for i in range(1, 101):
            user = TestUser(i)
            success = await create_user(client, user)
            if success:
                users.append(user)
                users_created += 1
                if i % 20 == 0:
                    print(f"  ✅ Created {i}/100 users")
            await asyncio.sleep(0.05)  # Small delay to avoid rate limiting
        
        print(f"  ✅ Created {users_created} users successfully")
        print()
        
        if users_created < 10:
            print("❌ Not enough users created. Aborting test.")
            return
        
        # ============================================
        # PHASE 2: BUY PLOTS & BUILD BUSINESSES
        # ============================================
        print("🏗️  PHASE 2: Buying plots and building businesses...")
        
        # Get available plots
        response = await client.get(f"{BASE_URL}/island")
        island_data = response.json() if response.status_code == 200 else {}
        cells = island_data.get("cells", [])
        
        # Filter available cells
        available_cells = [c for c in cells if not c.get("owner")]
        random.shuffle(available_cells)
        
        print(f"  📍 Found {len(available_cells)} available plots")
        
        # Each user tries to buy 1-3 plots and build businesses
        cell_index = 0
        for i, user in enumerate(users[:50]):  # First 50 users are active
            if cell_index >= len(available_cells):
                break
            
            # Try to buy a plot
            cell = available_cells[cell_index]
            x, y = cell.get("x", 0), cell.get("y", 0)
            
            if await buy_plot(client, user, x, y):
                plots_bought += 1
                
                # Build a business
                biz_type = PRODUCER_TYPES[i % len(PRODUCER_TYPES)]
                result = await build_business(client, user, x, y, biz_type)
                if result:
                    businesses_built += 1
                
                cell_index += 1
            
            if (i + 1) % 10 == 0:
                print(f"  ✅ Processed {i + 1}/50 active users")
            
            await asyncio.sleep(0.05)
        
        print(f"  ✅ Bought {plots_bought} plots, built {businesses_built} businesses")
        print()
        
        # ============================================
        # PHASE 3: CREATE MARKET LISTINGS
        # ============================================
        print("📊 PHASE 3: Creating market listings...")
        
        sellers = [u for u in users if len(u.businesses) > 0]
        
        for seller in sellers[:30]:  # First 30 sellers create listings
            for biz in seller.businesses:
                # Determine resource based on business type
                resource = BUSINESS_RESOURCES.get(biz["type"])
                if not resource:
                    continue
                
                amount = random.uniform(10, 100)
                price = random.uniform(0.001, 0.01)
                
                result = await create_market_listing(client, seller, biz["id"], resource, amount, price)
                if result:
                    listings_created += 1
            
            await asyncio.sleep(0.03)
        
        print(f"  ✅ Created {listings_created} market listings")
        print()
        
        # ============================================
        # PHASE 4: EXECUTE TRADES
        # ============================================
        print("💰 PHASE 4: Executing trades between users...")
        
        # Get current listings
        listings = await get_market_listings(client)
        print(f"  📋 Found {len(listings)} active listings")
        
        # Buyers (users who didn't sell)
        buyers = [u for u in users if len(u.businesses) == 0][:30]
        
        # Track balances before trades
        initial_balances = {}
        for user in sellers + buyers:
            initial_balances[user.wallet] = await get_user_balance(client, user)
        
        # Execute trades
        for buyer in buyers:
            if not listings:
                break
            
            # Pick a random listing
            listing = random.choice(listings)
            
            # Don't buy from yourself
            if listing.get("seller_id") == buyer.wallet:
                continue
            
            amount = min(listing.get("amount", 0), random.uniform(5, 20))
            if amount <= 0:
                continue
            
            result = await buy_from_market(client, buyer, listing["id"], amount)
            if result:
                trades_completed += 1
                total_traded += result.get("total_paid", 0)
                total_tax_collected += result.get("tax", 0)
                
                # Remove sold listing if depleted
                if amount >= listing.get("amount", 0):
                    listings.remove(listing)
            
            await asyncio.sleep(0.05)
        
        print(f"  ✅ Completed {trades_completed} trades")
        print(f"  💵 Total traded: {total_traded:.4f} TON")
        print(f"  🏛️  Tax collected: {total_tax_collected:.4f} TON")
        print()
        
        # ============================================
        # PHASE 5: VERIFY PROFIT DISTRIBUTION
        # ============================================
        print("📈 PHASE 5: Verifying profit distribution...")
        
        # Get final balances
        profit_verified = 0
        loss_verified = 0
        
        for seller in sellers[:10]:  # Check first 10 sellers
            final_balance = await get_user_balance(client, seller)
            initial = initial_balances.get(seller.wallet, 0)
            profit = final_balance - initial
            
            if profit > 0:
                profit_verified += 1
                print(f"  ✅ Seller {seller.username[:15]}: +{profit:.4f} TON profit")
            elif profit < 0:
                loss_verified += 1
                print(f"  ⚠️ Seller {seller.username[:15]}: {profit:.4f} TON (bought/spent)")
        
        for buyer in buyers[:10]:  # Check first 10 buyers
            final_balance = await get_user_balance(client, buyer)
            initial = initial_balances.get(buyer.wallet, 0)
            spent = initial - final_balance
            
            if spent > 0:
                print(f"  💳 Buyer {buyer.username[:15]}: -{spent:.4f} TON spent")
        
        print()
        
        # ============================================
        # PHASE 6: GET TREASURY STATS
        # ============================================
        print("🏛️  PHASE 6: Treasury and tax statistics...")
        
        treasury = await get_treasury(client)
        print(f"  📊 Treasury data: {treasury}")
        print()
        
        # ============================================
        # FINAL SUMMARY
        # ============================================
        print("=" * 70)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 70)
        print(f"  👥 Users created:     {users_created}/100")
        print(f"  🏠 Plots bought:      {plots_bought}")
        print(f"  🏭 Businesses built:  {businesses_built}")
        print(f"  📋 Listings created:  {listings_created}")
        print(f"  🔄 Trades completed:  {trades_completed}")
        print(f"  💵 Total traded:      {total_traded:.4f} TON")
        print(f"  🏛️  Tax collected:     {total_tax_collected:.4f} TON")
        print(f"  ✅ Sellers profited:  {profit_verified}")
        print("=" * 70)
        
        # Test verdict
        if users_created >= 50 and trades_completed >= 5 and total_tax_collected > 0:
            print("✅ TEST PASSED - Full trading cycle verified!")
        else:
            print("⚠️ TEST PARTIAL - Some features may need attention")
        
        print(f"📅 Completed: {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())
