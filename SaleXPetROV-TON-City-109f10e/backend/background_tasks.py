"""
Background Tasks Module
Handles scheduled tasks like automatic income collection
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

# MongoDB connection for background tasks
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'test_database')

# Global scheduler instance
scheduler: AsyncIOScheduler = None

# Tax configuration
BASE_TAX_RATE = 0.13

# Level configuration for income multipliers
LEVEL_CONFIG = {
    1: {"income_mult": 1.0},
    2: {"income_mult": 1.2},
    3: {"income_mult": 1.5},
    4: {"income_mult": 1.8},
    5: {"income_mult": 2.2},
    6: {"income_mult": 2.7},
    7: {"income_mult": 3.3},
    8: {"income_mult": 4.0},
    9: {"income_mult": 5.0},
    10: {"income_mult": 6.5},
}

# Business types configuration (base income)
BUSINESS_BASE_INCOME = {
    "farm": 2.4,
    "power_plant": 2.4,
    "quarry": 6.0,
    "oil_rig": 8.0,
    "mine": 7.0,
    "factory": 2.88,
    "construction_company": 5.0,
    "refinery": 10.0,
    "steel_mill": 9.0,
    "textile_factory": 4.0,
    "shop": 4.8,
    "restaurant": 5.4,
    "hotel": 8.0,
    "hospital": 12.0,
    "university": 10.0,
    "logistics_center": 6.0,
    "gas_station": 4.0,
    "bank": 4.5,
    "exchange": 20.0,
    "tech_hub": 15.0,
    "data_center": 18.0,
    "insurance": 6.0,
}

BUSINESS_OPERATING_COST = {
    "farm": 0.3,
    "power_plant": 0.8,
    "quarry": 1.5,
    "oil_rig": 2.0,
    "mine": 1.8,
    "factory": 1.44,
    "construction_company": 1.0,
    "refinery": 3.0,
    "steel_mill": 2.5,
    "textile_factory": 1.2,
    "shop": 0.5,
    "restaurant": 0.86,
    "hotel": 2.0,
    "hospital": 4.0,
    "university": 3.0,
    "logistics_center": 1.5,
    "gas_station": 1.0,
    "bank": 0.6,
    "exchange": 3.0,
    "tech_hub": 4.0,
    "data_center": 6.0,
    "insurance": 1.0,
}


async def calculate_business_income(business_type: str, level: int, connections: int) -> dict:
    """Calculate business income with all factors"""
    base_income = BUSINESS_BASE_INCOME.get(business_type, 0)
    operating_cost = BUSINESS_OPERATING_COST.get(business_type, 0)
    
    # Level multiplier
    level_mult = LEVEL_CONFIG.get(level, LEVEL_CONFIG[1])["income_mult"]
    
    # Connection bonus (+20% per connection)
    connection_mult = 1 + connections * 0.2
    
    gross_income = base_income * level_mult * connection_mult
    net_income = (gross_income - operating_cost * level_mult) * (1 - BASE_TAX_RATE)
    
    return {
        "gross": round(gross_income, 2),
        "operating_cost": round(operating_cost * level_mult, 2),
        "tax": round((gross_income - operating_cost * level_mult) * BASE_TAX_RATE, 2),
        "net": round(net_income, 2),
    }


async def auto_collect_income():
    """
    Automatically collect income from all active businesses
    Runs once per day
    """
    try:
        logger.info("🤖 Starting automatic income collection...")
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Get all active businesses that are fully built
        businesses_cursor = db.businesses.find({
            "is_active": True,
            "building_progress": {"$gte": 100}
        })
        businesses = await businesses_cursor.to_list(length=None)
        
        total_collected = 0
        businesses_processed = 0
        
        for business in businesses:
            try:
                business_id = business["id"]
                owner = business["owner"]
                business_type = business["business_type"]
                level = business.get("level", 1)
                connections = len(business.get("connected_businesses", []))
                
                # Get last collection time
                last_collection_str = business.get("last_collection")
                if isinstance(last_collection_str, str):
                    last_collection = datetime.fromisoformat(last_collection_str)
                else:
                    last_collection = last_collection_str
                
                # Calculate time passed
                now = datetime.now(timezone.utc)
                hours_passed = (now - last_collection).total_seconds() / 3600
                days_passed = hours_passed / 24
                
                # Skip if less than 1 hour passed (safety check)
                if hours_passed < 1:
                    continue
                
                # Calculate income
                income_data = await calculate_business_income(business_type, level, connections)
                
                gross_income = income_data["gross"] * days_passed
                tax = income_data["tax"] * days_passed
                net_income = income_data["net"] * days_passed
                
                # Update business
                await db.businesses.update_one(
                    {"id": business_id},
                    {
                        "$set": {"last_collection": now.isoformat()},
                        "$inc": {"xp": int(gross_income * 10)}
                    }
                )
                
                # Update user balance
                await db.users.update_one(
                    {"wallet_address": owner},
                    {
                        "$inc": {
                            "balance_game": net_income,
                            "total_income": net_income
                        }
                    }
                )
                
                # Record tax
                await db.admin_stats.update_one(
                    {"type": "treasury"},
                    {"$inc": {"total_tax": tax}},
                    upsert=True
                )
                
                total_collected += net_income
                businesses_processed += 1
                
                logger.info(f"✅ Collected {net_income:.4f} TON from {business_type} (owner: {owner[:8]}...)")
                
            except Exception as e:
                logger.error(f"❌ Failed to collect income for business {business.get('id')}: {e}")
                continue
        
        # Log summary
        logger.info(f"🎉 Auto-collection complete!")
        logger.info(f"   📊 Processed: {businesses_processed} businesses")
        logger.info(f"   💰 Total collected: {total_collected:.4f} TON")
        
        # Record auto-collection event
        await db.system_events.insert_one({
            "type": "auto_income_collection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "businesses_processed": businesses_processed,
            "total_collected": total_collected
        })
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Auto-collection failed: {e}")
        raise


def init_scheduler():
    """Initialize APScheduler for background tasks"""
    global scheduler
    
    scheduler = AsyncIOScheduler()
    
    # Schedule automatic income collection daily at 00:00 UTC
    scheduler.add_job(
        auto_collect_income,
        trigger=CronTrigger(hour=0, minute=0),
        id="auto_collect_income",
        name="Automatic Income Collection",
        replace_existing=True
    )
    
    logger.info("✅ Scheduler initialized")
    logger.info("📅 Auto-collection scheduled: Daily at 00:00 UTC")
    
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


# Manual trigger for testing
async def trigger_auto_collection_now():
    """Manually trigger income collection (for testing)"""
    logger.info("🔧 Manually triggering auto-collection...")
    await auto_collect_income()
