"""
TON-City Background Tasks V2.0 - Complete Economic Tick Engine
Handles: Auto-collection, Midnight Decay, Durability Wear,
NPC Interventions, Price Updates, Bankruptcy Checks, Events

TICK ORDER:
1. Production
2. Resource purchasing (consumption)
3. Maintenance deduction
4. Profit calculation
5. Income tax
6. Turnover tax
7. NPC consumption
8. Price updates
9. Monopoly check
10. Inflation
11. Bankruptcy check
12. Events
13. Save snapshot
"""
import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from motor.motor_asyncio import AsyncIOMotorClient
import os

from business_config import (
    BUSINESSES, TIER_TAXES, MAINTENANCE_COSTS, RESOURCE_TYPES,
    BUSINESS_LEVELS, MIDNIGHT_DECAY_RATE,
    NPC_PRICE_FLOOR, NPC_PRICE_CEILING, MONOPOLY_THRESHOLD,
    get_production, get_consumption, get_consumption_breakdown,
    calculate_effective_production, get_daily_wear, get_storage_capacity,
)
from game_systems import (
    BusinessEconomics, TaxSystem, NPCMarketSystem, WarehouseSystem,
    InflationSystem, BankruptcySystem, EventsSystem, EconomicTickEngine,
    IncomeCollector,
)

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'ton_city')

# Global scheduler
scheduler: AsyncIOScheduler = None


# ==================== MAIN ECONOMIC TICK ====================

async def economic_tick():
    """
    Main economic tick - runs every hour.
    Processes all active businesses through the 13-step pipeline.
    """
    try:
        logger.info("⚙️ === ECONOMIC TICK STARTED ===")
        
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        now = datetime.now(timezone.utc)
        
        # Get all active businesses
        businesses = await db.businesses.find({"is_active": True}).to_list(length=None)
        
        if not businesses:
            logger.info("📊 No active businesses - tick skipped")
            client.close()
            return
        
        # Get current market prices
        market_prices_doc = await db.market_prices.find_one({"type": "current"})
        market_prices = {}
        if market_prices_doc:
            market_prices = market_prices_doc.get("prices", {})
        else:
            # Initialize with base prices
            market_prices = {r: d["base_price"] for r, d in RESOURCE_TYPES.items()}
            await db.market_prices.update_one(
                {"type": "current"},
                {"$set": {"prices": market_prices, "updated_at": now.isoformat()}},
                upsert=True
            )
        
        # Get all users
        users = {}
        users_cursor = db.users.find({})
        async for user in users_cursor:
            wallet = user.get("wallet_address") or user.get("id")
            if wallet:
                users[wallet] = user
        
        # Track totals
        total_tax_collected = 0
        total_maintenance_collected = 0
        total_production = {}
        total_consumption = {}
        tick_results = []
        businesses_processed = 0
        
        # === PROCESS EACH BUSINESS (Steps 1-6) ===
        for business in businesses:
            try:
                business_id = business.get("id")
                owner = business.get("owner")
                business_type = business.get("business_type")
                level = business.get("level", 1)
                durability = business.get("durability", 100)
                
                if not business_type or business_type not in BUSINESSES:
                    continue
                
                config = BUSINESSES.get(business_type, {})
                tier = config.get("tier", 1)
                
                # Calculate time since last tick
                last_tick = business.get("last_tick") or business.get("last_collection")
                hours_passed = 1.0  # Default to 1 hour
                if last_tick:
                    try:
                        last_dt = datetime.fromisoformat(str(last_tick).replace('Z', '+00:00'))
                        hours_passed = max(0.1, (now - last_dt).total_seconds() / 3600)
                    except (ValueError, TypeError):
                        hours_passed = 1.0
                
                # Skip if less than 30 min since last tick
                if hours_passed < 0.5:
                    continue
                
                # --- Step 1: Apply durability wear ---
                wear_result = BusinessEconomics.apply_wear(business, hours_passed)
                new_durability = wear_result["durability"]
                
                # --- Step 1b: Production ---
                business_copy = {**business, "durability": new_durability}
                patron_bonus = 1.0
                if business.get("patron_id"):
                    patron_bonus = 1.1  # Simplified patron bonus
                
                effective_prod = calculate_effective_production(
                    business_type, level, new_durability, patron_bonus
                )
                produces = config.get("produces")
                
                # Scale production by hours passed (production values are per-tick/day)
                hourly_fraction = hours_passed / 24.0
                actual_production = effective_prod * hourly_fraction
                
                # --- Step 2: Consumption ---
                consumption_breakdown = get_consumption_breakdown(business_type, level)
                # Scale consumption by hours
                scaled_consumption = {r: int(a * hourly_fraction) for r, a in consumption_breakdown.items()}
                
                # Check user's resource inventory
                user = users.get(owner, {})
                user_resources = user.get("resources", {})
                
                can_operate = True
                for resource, required in scaled_consumption.items():
                    if user_resources.get(resource, 0) < required:
                        can_operate = False
                        break
                
                if not can_operate:
                    actual_production = 0
                
                # --- Step 3: Maintenance ---
                maintenance = MAINTENANCE_COSTS.get(tier, {}).get(level, 0.05)
                maintenance_cost = maintenance * hourly_fraction
                
                # --- Step 4: Profit ---
                if produces in ("ton", "profit_ton"):
                    gross_profit = actual_production * 0.01
                elif produces and produces in market_prices:
                    gross_profit = actual_production * max(0.01, market_prices.get(produces, 0.01))
                else:
                    gross_profit = 0
                
                # --- Step 5: Income tax ---
                tax_rate = TIER_TAXES.get(tier, 0.15)
                income_tax = gross_profit * tax_rate
                
                # --- Step 6: Patron tax ---
                has_patron = business.get("patron_id") is not None
                patron_tax = (gross_profit - income_tax) * 0.01 if has_patron else 0
                
                # Net income to player
                net_income = gross_profit - income_tax - patron_tax - maintenance_cost
                
                # --- Update business in DB ---
                update_ops = {
                    "$set": {
                        "durability": new_durability,
                        "last_tick": now.isoformat(),
                        "last_collection": now.isoformat(),
                        "last_wear_update": now.isoformat(),
                    }
                }
                
                if actual_production > 0 and produces:
                    if produces not in ("ton", "profit_ton"):
                        # Add produced resource to user inventory
                        update_ops.setdefault("$inc", {})
                        # We'll update user resources separately
                    
                await db.businesses.update_one({"id": business_id}, update_ops)
                
                # --- Update user ---
                user_update = {"$inc": {}}
                
                # Add net income
                if net_income != 0:
                    user_update["$inc"]["balance_ton"] = round(net_income, 6)
                    user_update["$inc"]["total_income"] = round(max(0, net_income), 6)
                
                # Add produced resources to inventory
                if can_operate and actual_production > 0 and produces and produces not in ("ton", "profit_ton"):
                    user_update["$inc"][f"resources.{produces}"] = round(actual_production, 2)
                
                # Deduct consumed resources
                if can_operate:
                    for resource, amount in scaled_consumption.items():
                        if amount > 0:
                            user_update["$inc"][f"resources.{resource}"] = -amount
                
                if user_update["$inc"]:
                    await db.users.update_one(
                        {"$or": [{"wallet_address": owner}, {"id": owner}]},
                        user_update
                    )
                
                # Track totals
                total_tax_collected += income_tax + patron_tax
                total_maintenance_collected += maintenance_cost
                
                if produces and actual_production > 0:
                    total_production[produces] = total_production.get(produces, 0) + actual_production
                for r, a in scaled_consumption.items():
                    if can_operate:
                        total_consumption[r] = total_consumption.get(r, 0) + a
                
                tick_results.append({
                    "business_id": business_id,
                    "type": business_type,
                    "owner": owner,
                    "net_income": round(net_income, 6),
                    "production": round(actual_production, 2),
                    "produces": produces,
                    "maintenance": round(maintenance_cost, 6),
                    "tax": round(income_tax, 6),
                    "durability": new_durability,
                })
                
                businesses_processed += 1
                
            except Exception as e:
                logger.error(f"❌ Tick error for business {business.get('id')}: {e}")
                continue
        
        # === GLOBAL STEPS (7-13) ===
        
        # Step 7: NPC consumption
        total_supply = {}
        supply_cursor = db.users.aggregate([
            {"$project": {"resources": 1}},
        ])
        async for doc in supply_cursor:
            for r, a in doc.get("resources", {}).items():
                total_supply[r] = total_supply.get(r, 0) + a
        
        npc_consumed = NPCMarketSystem.calculate_npc_consumption(total_supply)
        
        # Step 8: Price updates / NPC interventions
        interventions = []
        for resource, price in market_prices.items():
            intervention = NPCMarketSystem.check_price_intervention(resource, price)
            if intervention:
                interventions.append(intervention)
                # Adjust price towards base
                base_price = RESOURCE_TYPES.get(resource, {}).get("base_price", price)
                if intervention["action"] == "buy":
                    market_prices[resource] = price * 1.05  # Push price up 5%
                else:
                    market_prices[resource] = price * 0.95  # Push price down 5%
        
        # Step 10: Inflation
        total_ton_produced = sum(r.get("net_income", 0) for r in tick_results if r.get("net_income", 0) > 0)
        total_ton_sunk = total_tax_collected + total_maintenance_collected
        inflation_factor = InflationSystem.calculate_inflation_factor(total_ton_produced, total_ton_sunk)
        market_prices = InflationSystem.apply_price_inflation(market_prices, inflation_factor)
        
        # Save updated prices
        await db.market_prices.update_one(
            {"type": "current"},
            {"$set": {"prices": market_prices, "updated_at": now.isoformat()}},
            upsert=True
        )
        
        # Step 11: Bankruptcy checks
        bankruptcies = []
        async for user in db.users.find({"balance_ton": {"$lt": -10}}):
            bankruptcy = BankruptcySystem.check_bankruptcy(user)
            if bankruptcy["is_bankrupt"]:
                bankruptcies.append({
                    "user": user.get("wallet_address") or user.get("id"),
                    "balance": user.get("balance_ton"),
                    "reason": bankruptcy["reason"],
                })
                # Pause all their businesses
                await db.businesses.update_many(
                    {"owner": user.get("wallet_address") or user.get("id")},
                    {"$set": {"is_active": False, "paused_reason": "bankruptcy"}}
                )
        
        # Step 12: Events
        events = EventsSystem.roll_events()
        
        # Step 13: Save snapshot
        await db.admin_stats.update_one(
            {"type": "treasury"},
            {"$inc": {
                "total_tax": total_tax_collected,
                "total_maintenance": total_maintenance_collected,
            }},
            upsert=True
        )
        
        snapshot = {
            "type": "tick_snapshot",
            "timestamp": now.isoformat(),
            "businesses_processed": businesses_processed,
            "total_tax_collected": round(total_tax_collected, 4),
            "total_maintenance_collected": round(total_maintenance_collected, 4),
            "total_production": {k: round(v, 2) for k, v in total_production.items()},
            "total_consumption": {k: round(v, 2) for k, v in total_consumption.items()},
            "npc_consumed": npc_consumed,
            "npc_interventions": len(interventions),
            "inflation_factor": round(inflation_factor, 6),
            "bankruptcies": len(bankruptcies),
            "events": [e.get("id") for e in events],
            "market_prices": market_prices,
        }
        
        await db.economic_snapshots.insert_one(snapshot)
        
        # Log summary
        logger.info(f"✅ TICK COMPLETE:")
        logger.info(f"   📊 Businesses: {businesses_processed}")
        logger.info(f"   💰 Tax: {total_tax_collected:.4f} TON")
        logger.info(f"   🔧 Maintenance: {total_maintenance_collected:.4f} TON")
        logger.info(f"   📈 Inflation: {inflation_factor:.4f}x")
        logger.info(f"   ⚠️ Bankruptcies: {len(bankruptcies)}")
        logger.info(f"   🎲 Events: {len(events)}")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ ECONOMIC TICK FAILED: {e}")
        import traceback
        logger.error(traceback.format_exc())


# ==================== MIDNIGHT DECAY ====================

async def midnight_decay():
    """
    Apply 10% decay to all inventories at 00:00 MSK (21:00 UTC).
    Stimulates daily sales and market activity.
    """
    try:
        logger.info("🌙 === MIDNIGHT DECAY STARTED ===")
        
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        users_cursor = db.users.find({"resources": {"$exists": True}})
        decayed_count = 0
        total_lost = {}
        
        async for user in users_cursor:
            resources = user.get("resources", {})
            if not resources:
                continue
            
            new_resources = {}
            for resource, amount in resources.items():
                if isinstance(amount, (int, float)) and amount > 0:
                    lost = int(amount * MIDNIGHT_DECAY_RATE)
                    new_resources[resource] = max(0, amount - lost)
                    total_lost[resource] = total_lost.get(resource, 0) + lost
                else:
                    new_resources[resource] = amount
            
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"resources": new_resources}}
            )
            decayed_count += 1
        
        # Log
        logger.info(f"🌙 Decay applied to {decayed_count} users")
        for r, lost in total_lost.items():
            if lost > 0:
                logger.info(f"   🔻 {r}: -{lost}")
        
        # Save decay event
        await db.system_events.insert_one({
            "type": "midnight_decay",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "users_affected": decayed_count,
            "resources_lost": total_lost,
        })
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ MIDNIGHT DECAY FAILED: {e}")


# ==================== DURABILITY WEAR ====================

async def apply_global_durability_wear():
    """Apply durability wear to all businesses based on time elapsed"""
    try:
        logger.info("🔧 Applying durability wear...")
        
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        businesses = await db.businesses.find({"is_active": True}).to_list(length=None)
        now = datetime.now(timezone.utc)
        
        for business in businesses:
            business_type = business.get("business_type")
            level = business.get("level", 1)
            current_durability = business.get("durability", 100)
            
            if current_durability <= 0:
                continue
            
            # Calculate hours since last wear update
            last_update = business.get("last_wear_update") or business.get("last_tick")
            hours_passed = 1.0
            if last_update:
                try:
                    last_dt = datetime.fromisoformat(str(last_update).replace('Z', '+00:00'))
                    hours_passed = (now - last_dt).total_seconds() / 3600
                except (ValueError, TypeError):
                    hours_passed = 1.0
            
            daily_wear = get_daily_wear(business_type, level)
            wear_amount = daily_wear * 100 * (hours_passed / 24.0)
            new_durability = max(0, current_durability - wear_amount)
            
            await db.businesses.update_one(
                {"id": business.get("id")},
                {"$set": {
                    "durability": round(new_durability, 2),
                    "last_wear_update": now.isoformat(),
                }}
            )
        
        logger.info(f"🔧 Wear applied to {len(businesses)} businesses")
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Durability wear failed: {e}")


# ==================== BACKWARD COMPATIBLE FUNCTIONS ====================

async def calculate_business_income(business_type: str, level: int, connections: int) -> dict:
    """Backward compatible income calculation using new data"""
    production = get_production(business_type, level)
    consumption = get_consumption(business_type, level)
    config = BUSINESSES.get(business_type, {})
    tier = config.get("tier", 1)
    
    connection_mult = 1 + connections * 0.1
    
    # Base market price for the produced resource
    produces = config.get("produces", "")
    from business_config import RESOURCE_TYPES as RT
    base_price = RT.get(produces, {}).get("base_price", 0.01)
    
    gross_value = production * base_price * connection_mult
    tax_rate = TIER_TAXES.get(tier, 0.15)
    maintenance = MAINTENANCE_COSTS.get(tier, {}).get(level, 0.05)
    
    net = gross_value * (1 - tax_rate) - maintenance
    
    return {
        "gross": round(gross_value, 4),
        "operating_cost": round(maintenance, 4),
        "tax": round(gross_value * tax_rate, 4),
        "net": round(net, 4),
    }


async def auto_collect_income():
    """Run the full economic tick (backward compatible wrapper)"""
    await economic_tick()


# ==================== SCHEDULER ====================

# ==================== CREDIT PROCESSING ====================

async def process_credits():
    """
    Daily credit processing:
    1. Deduct salary percentage from income for active credits
    2. Detect overdue credits (no payment in specified days)
    3. Double rate for overdue credits
    4. Seize businesses after 7 days of non-payment
    """
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        now = datetime.now(timezone.utc)
        active_credits = await db.credits.find(
            {"status": {"$in": ["active", "overdue"]}},
            {"_id": 0}
        ).to_list(500)
        
        logger.info(f"💰 Processing {len(active_credits)} active credits...")
        
        for credit in active_credits:
            credit_id = credit["id"]
            borrower_id = credit.get("borrower_id", "")
            borrower_wallet = credit.get("borrower_wallet", "")
            remaining = credit.get("remaining", 0)
            deduction_pct = credit.get("salary_deduction_percent", 0.10)
            
            if remaining <= 0:
                await db.credits.update_one({"id": credit_id}, {"$set": {"status": "paid", "remaining": 0}})
                continue
            
            # Find borrower
            borrower = await db.users.find_one(
                {"$or": [{"id": borrower_id}, {"wallet_address": borrower_wallet}]},
                {"_id": 0}
            )
            if not borrower:
                continue
            
            # Calculate daily payment from income
            balance = borrower.get("balance_ton", 0)
            daily_income = borrower.get("total_income", 0) / max(1, (now - datetime.fromisoformat(borrower.get("created_at", now.isoformat()).replace("Z", "+00:00"))).days or 1)
            
            # Calculate payment amount
            payment = round(daily_income * deduction_pct, 4)
            
            # If overdue and doubled rate active, double the payment
            if credit.get("is_doubled_rate"):
                payment *= 2
            
            # Limit payment to available balance and remaining debt
            payment = min(payment, balance, remaining)
            
            if payment > 0.0001:
                # Deduct from borrower
                user_filter = {"id": borrower_id} if borrower_id else {"wallet_address": borrower_wallet}
                await db.users.update_one(user_filter, {"$inc": {"balance_ton": -payment}})
                
                new_remaining = round(remaining - payment, 4)
                new_paid = round(credit.get("paid", 0) + payment, 4)
                
                update_set = {
                    "remaining": max(0, new_remaining),
                    "paid": new_paid,
                    "last_payment": now.isoformat(),
                }
                
                if new_remaining <= 0:
                    update_set["status"] = "paid"
                    update_set["remaining"] = 0
                
                await db.credits.update_one({"id": credit_id}, {"$set": update_set})
                
                # Pay to lender if bank
                if credit.get("lender_type") == "bank" and credit.get("lender_id"):
                    await db.users.update_one(
                        {"$or": [{"id": credit["lender_id"]}, {"wallet_address": credit["lender_id"]}]},
                        {"$inc": {"balance_ton": payment}}
                    )
                
                logger.info(f"  Credit {credit_id[:8]}: payment {payment:.4f} TON, remaining {new_remaining:.2f}")
            
            # Check overdue status
            last_payment = credit.get("last_payment")
            overdue_days = credit.get("overdue_penalty_days", 3)
            
            if last_payment:
                try:
                    lp = datetime.fromisoformat(last_payment.replace("Z", "+00:00"))
                    days_since = (now - lp).days
                except Exception:
                    days_since = 0
            else:
                created = credit.get("created_at", now.isoformat())
                try:
                    cr = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    days_since = (now - cr).days
                except Exception:
                    days_since = 0
            
            # Activate doubled rate after overdue_penalty_days
            if days_since >= overdue_days and not credit.get("is_doubled_rate") and payment < 0.0001:
                await db.credits.update_one({"id": credit_id}, {"$set": {
                    "status": "overdue",
                    "is_doubled_rate": True,
                    "overdue_since": credit.get("overdue_since") or now.isoformat(),
                }})
                logger.warning(f"  ⚠️ Credit {credit_id[:8]}: OVERDUE - doubled rate activated")
                
                # Send notification
                await db.notifications.insert_one({
                    "user_id": borrower_id,
                    "type": "credit_overdue",
                    "message": f"Кредит просрочен! Ставка удвоена. Погасите долг {remaining:.2f} TON.",
                    "created_at": now.isoformat(),
                    "read": False,
                })
            
            # Seize business after 7 days of non-payment
            overdue_since = credit.get("overdue_since")
            if overdue_since:
                try:
                    os_dt = datetime.fromisoformat(overdue_since.replace("Z", "+00:00"))
                    overdue_total_days = (now - os_dt).days
                except Exception:
                    overdue_total_days = 0
                
                if overdue_total_days >= 7 and credit.get("status") == "overdue":
                    # SEIZE BUSINESS
                    biz_id = credit.get("collateral_business_id")
                    business = await db.businesses.find_one({"id": biz_id}, {"_id": 0})
                    
                    if business:
                        lender_type = credit.get("lender_type", "government")
                        lender_id = credit.get("lender_id", "government")
                        
                        if lender_type == "government":
                            # Auto-sell at -20%
                            collateral_value = credit.get("collateral_value", 0)
                            sale_price = round(collateral_value * 0.80, 2)
                            
                            await db.businesses.update_one({"id": biz_id}, {"$set": {
                                "owner": "government",
                                "owner_wallet": "government",
                                "for_sale": True,
                                "sale_price": sale_price,
                                "seized_from": borrower_id,
                                "seized_at": now.isoformat(),
                            }})
                            
                            # Also list on land marketplace if plot exists
                            plot_id = business.get("plot_id")
                            if plot_id:
                                plot = await db.plots.find_one({"id": plot_id}, {"_id": 0})
                                if plot:
                                    listing_id = str(uuid.uuid4())
                                    listing = {
                                        "id": listing_id,
                                        "plot_id": plot_id,
                                        "city_id": plot.get("island_id", "ton_island"),
                                        "city_name": "TON Island",
                                        "x": plot.get("x", 0),
                                        "y": plot.get("y", 0),
                                        "seller_id": "government",
                                        "seller_wallet": "government",
                                        "seller_username": "Государство",
                                        "price": sale_price,
                                        "business": {
                                            "id": biz_id,
                                            "type": business.get("type"),
                                            "level": business.get("level", 1),
                                            "tier": business.get("tier", 1)
                                        },
                                        "status": "active",
                                        "is_seized": True,
                                        "seized_from": borrower_id,
                                        "created_at": now.isoformat()
                                    }
                                    await db.land_listings.insert_one(listing)
                                    
                                    # Update plot owner to government
                                    await db.plots.update_one({"id": plot_id}, {"$set": {
                                        "owner": "government",
                                        "owner_wallet": "government",
                                        "seized_from": borrower_id
                                    }})
                                    
                                    logger.warning(f"  📢 Land listing created for seized business at {sale_price} TON")
                            
                            logger.warning(f"  🏛️ Business {biz_id[:8]} SEIZED by government, listed at {sale_price} TON")
                        else:
                            # Transfer to bank owner
                            await db.businesses.update_one({"id": biz_id}, {"$set": {
                                "owner": lender_id,
                                "owner_wallet": lender_id,
                                "seized_from": borrower_id,
                                "seized_at": now.isoformat(),
                            }})
                            
                            logger.warning(f"  🏦 Business {biz_id[:8]} SEIZED by bank owner {lender_id[:8]}")
                        
                        # Mark credit as seized
                        await db.credits.update_one({"id": credit_id}, {"$set": {
                            "status": "seized",
                            "remaining": 0,
                            "seized_at": now.isoformat(),
                        }})
                        
                        # Notify borrower
                        await db.notifications.insert_one({
                            "user_id": borrower_id,
                            "type": "business_seized",
                            "message": f"Ваш бизнес конфискован за неуплату кредита!",
                            "created_at": now.isoformat(),
                            "read": False,
                        })
        
        logger.info(f"✅ Credit processing complete")
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Credit processing error: {e}")


# ==================== WAREHOUSE SPOILAGE ====================

async def process_warehouse_spoilage():
    """
    Daily warehouse spoilage:
    If user's total warehouse usage exceeds capacity,
    50% of the overflow is destroyed each day.
    """
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        now = datetime.now(timezone.utc)
        
        # Get all users with businesses
        users = await db.users.find({}, {"_id": 0, "id": 1, "wallet_address": 1, "username": 1}).to_list(1000)
        
        spoiled_count = 0
        
        for user in users:
            uid = user.get("id", "")
            wallet = user.get("wallet_address", "")
            
            # Get businesses
            or_q = [{"owner": uid}]
            if wallet:
                or_q.append({"owner": wallet})
            
            businesses = await db.businesses.find({"$or": or_q}, {"_id": 0}).to_list(50)
            if not businesses:
                continue
            
            # Calculate total capacity and usage
            total_capacity = 0
            total_used = 0
            biz_items = []  # [(biz_id, resource, amount)]
            
            for biz in businesses:
                storage = biz.get("storage", {})
                total_capacity += storage.get("capacity", 0)
                items = storage.get("items", {})
                for resource, amount in items.items():
                    amt = int(amount)
                    if amt > 0:
                        total_used += amt
                        biz_items.append((biz["id"], resource, amt))
            
            overflow = total_used - total_capacity
            if overflow <= 0:
                continue
            
            # 50% of overflow is destroyed
            spoilage = int(overflow * 0.5)
            if spoilage <= 0:
                continue
            
            # Distribute spoilage proportionally across items
            remaining_spoil = spoilage
            for biz_id, resource, amount in sorted(biz_items, key=lambda x: -x[2]):
                if remaining_spoil <= 0:
                    break
                destroy = min(remaining_spoil, amount)
                await db.businesses.update_one(
                    {"id": biz_id},
                    {"$inc": {f"storage.items.{resource}": -destroy}}
                )
                remaining_spoil -= destroy
            
            spoiled_count += 1
            logger.info(f"  🗑️ User {user.get('username', uid[:8])}: spoiled {spoilage} units (overflow: {overflow})")
            
            # Notify user
            await db.notifications.insert_one({
                "user_id": uid,
                "type": "warehouse_spoilage",
                "message": f"Склад переполнен! Испорчено {spoilage} единиц товара.",
                "created_at": now.isoformat(),
                "read": False,
            })
        
        logger.info(f"✅ Warehouse spoilage: {spoiled_count} users affected")
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Warehouse spoilage error: {e}")


# ==================== NOTIFICATIONS SENDER ====================

async def send_pending_notifications():
    """Send pending notifications via Telegram"""
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Get unread notifications for users with Telegram
        notifications = await db.notifications.find(
            {"read": False, "telegram_sent": {"$ne": True}},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        if not notifications:
            client.close()
            return
        
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            client.close()
            return
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            for notif in notifications:
                user_id = notif.get("user_id", "")
                user = await db.users.find_one(
                    {"$or": [{"id": user_id}, {"wallet_address": user_id}]},
                    {"_id": 0}
                )
                if not user or not user.get("telegram_username"):
                    continue
                
                # Get chat_id from stored mapping
                tg_mapping = await db.telegram_mappings.find_one(
                    {"username": user.get("telegram_username")},
                    {"_id": 0}
                )
                if not tg_mapping or not tg_mapping.get("chat_id"):
                    continue
                
                chat_id = tg_mapping["chat_id"]
                message = f"🏙️ TON City\n\n{notif.get('message', '')}"
                
                try:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    await session.post(url, json={
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "HTML"
                    })
                    
                    await db.notifications.update_one(
                        {"user_id": user_id, "created_at": notif["created_at"]},
                        {"$set": {"telegram_sent": True}}
                    )
                except Exception as e:
                    logger.error(f"Telegram send error: {e}")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Notification sender error: {e}")


def init_scheduler():
    """Initialize APScheduler with all background tasks"""
    global scheduler
    
    scheduler = AsyncIOScheduler()
    
    # Main economic tick - every hour
    scheduler.add_job(
        economic_tick,
        trigger=IntervalTrigger(hours=1),
        id="economic_tick",
        name="Economic Tick (Hourly)",
        replace_existing=True,
    )
    
    # Midnight decay - daily at 21:00 UTC (00:00 MSK)
    scheduler.add_job(
        midnight_decay,
        trigger=CronTrigger(hour=21, minute=0),
        id="midnight_decay",
        name="Midnight Decay (00:00 MSK)",
        replace_existing=True,
    )
    
    # Durability wear - every 6 hours (as backup, main wear happens in tick)
    scheduler.add_job(
        apply_global_durability_wear,
        trigger=IntervalTrigger(hours=6),
        id="durability_wear",
        name="Durability Wear Check",
        replace_existing=True,
    )
    
    # Credit processing - daily at 22:00 UTC (01:00 MSK)
    scheduler.add_job(
        process_credits,
        trigger=CronTrigger(hour=22, minute=0),
        id="credit_processing",
        name="Credit Processing Daily",
        replace_existing=True,
    )
    
    # Warehouse spoilage - daily at 21:30 UTC (00:30 MSK)
    scheduler.add_job(
        process_warehouse_spoilage,
        trigger=CronTrigger(hour=21, minute=30),
        id="warehouse_spoilage",
        name="Warehouse Spoilage Daily",
        replace_existing=True,
    )
    
    # Notification sender - every 5 minutes
    scheduler.add_job(
        send_pending_notifications,
        trigger=IntervalTrigger(minutes=5),
        id="notification_sender",
        name="Notification Sender",
        replace_existing=True,
    )
    
    logger.info("✅ Scheduler initialized with V2.0 economic engine")
    logger.info("📅 Economic Tick: Every 1 hour")
    logger.info("📅 Midnight Decay: Daily at 21:00 UTC (00:00 MSK)")
    logger.info("📅 Durability Wear: Every 6 hours")
    logger.info("📅 Credit Processing: Daily at 22:00 UTC")
    logger.info("📅 Warehouse Spoilage: Daily at 21:30 UTC")
    logger.info("📅 Notifications: Every 5 minutes")
    
    return scheduler


def start_scheduler():
    """Start the scheduler"""
    global scheduler
    if scheduler is None:
        init_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("🚀 Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Scheduler stopped")


async def trigger_auto_collection_now():
    """Manually trigger economic tick"""
    logger.info("🔧 Manual economic tick triggered...")
    await economic_tick()
