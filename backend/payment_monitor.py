"""
TON Payment Monitor
Monitors incoming TON transactions and credits internal balance
"""
import logging
import asyncio
from datetime import datetime, timezone
<<<<<<< HEAD
import os   
from tonsdk.utils import Address

def to_raw(address_str):
    try:
        return Address(address_str).to_string(is_user_friendly=False)
    except Exception:
        return address_str

=======
from motor.motor_asyncio import AsyncIOMotorClient
import os
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e

logger = logging.getLogger(__name__)

class TONPaymentMonitor:
    """Monitor TON blockchain for incoming payments"""
    
    def __init__(self, db):
        self.db = db
        self.is_running = False
        self.check_interval = 30  # seconds
        
    async def get_game_settings(self):
        """Get game wallet settings from database"""
        settings = await self.db.game_settings.find_one({"type": "ton_wallet"})
        if not settings:
            # Create default settings
            default_settings = {
                "type": "ton_wallet",
                "network": "testnet",  # testnet or mainnet
                "receiver_address": "",  # Admin sets this
                "last_checked_lt": 0,  # Logical time for transaction tracking
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db.game_settings.insert_one(default_settings)
            return default_settings
        return settings
    
    async def check_incoming_transactions(self):
<<<<<<< HEAD
=======
        """Check for new incoming TON transactions"""
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
        try:
            settings = await self.get_game_settings()
            receiver_address = settings.get("receiver_address")
            
            if not receiver_address:
<<<<<<< HEAD
                logger.warning("⚠️ Адрес получателя не настроен.")
                return
            
            from ton_integration import ton_client
            # Ton APIs may return sender/receiver in raw (0:...) format; keep both forms available.
            receiver_raw = to_raw(receiver_address)

            # Some providers expect user-friendly, some expect raw. Try user-friendly first, then raw.
            try:
                transactions = await ton_client.get_transaction_history(receiver_address, limit=20)
            except Exception:
                transactions = await ton_client.get_transaction_history(receiver_raw, limit=20)
            
            for tx in transactions:
                tx_hash = tx.get("transaction_id", {}).get("hash")
                in_msg = tx.get("in_msg", {})
                
                sender_address = in_msg.get("source") # Адрес кошелька плательщика (often raw: 0:...)
                value = int(in_msg.get("value", 0))    # Сумма в нанотоннах

                if value <= 0 or not sender_address:
                    continue

                sender_raw = to_raw(sender_address)
                user = await self.db.users.find_one({
                    "$or": [
                        {"wallet_address": sender_address},
                        {"raw_address": sender_address},
                        {"wallet_address": sender_raw},
                        {"raw_address": sender_raw},
                    ]
                }, {"_id": 0})

                if user:
                    # 3. Формируем данные для зачисления
                    tx_data = {
                        "hash": tx_hash,
                        "sender": sender_address,
                        "sender_raw": sender_raw,
                        "amount": value
                    }
                    # Зачисляем деньги пользователю
                    await self.process_incoming_payment(tx_data)
                else:
                    # Если кошелек не найден в базе
                    logger.debug(f"Платеж от неизвестного адреса: {sender_address}")

        except Exception as e:
            logger.error(f"❌ Error in monitor: {e}")
=======
                logger.warning("⚠️  No receiver address configured. Set in admin panel.")
                return
            
            network = settings.get("network", "testnet")
            logger.info(f"🔍 Checking {network} transactions for {receiver_address[:8]}...")
            
            # In production, here we would:
            # 1. Query TON blockchain API for transactions
            # 2. Filter transactions since last_checked_lt
            # 3. Process each incoming transaction
            
            # For now, simulate checking
            # In production, use TonCenter API or TON SDK
            
            logger.info(f"✅ Transaction check complete ({network})")
            
        except Exception as e:
            logger.error(f"❌ Error checking transactions: {e}")
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
    
    async def process_incoming_payment(self, transaction):
        """
        Process an incoming TON payment
        
        Args:
            transaction: Transaction data from blockchain
        """
        try:
            sender = transaction.get("sender")
<<<<<<< HEAD
            sender_raw = transaction.get("sender_raw") or to_raw(sender)
=======
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
            amount = transaction.get("amount")  # in nanoTON
            amount_ton = amount / 1e9
            tx_hash = transaction.get("hash")
            memo = transaction.get("memo", "")
            
            # Check if already processed
            existing = await self.db.deposits.find_one({"tx_hash": tx_hash})
            if existing:
                logger.info(f"⏭️  Transaction already processed: {tx_hash}")
                return
            
<<<<<<< HEAD
            # Try to find user by wallet address (support both user-friendly and raw formats)
            user = await self.db.users.find_one({
                "$or": [
                    {"wallet_address": sender},
                    {"raw_address": sender},
                    {"wallet_address": sender_raw},
                    {"raw_address": sender_raw},
                ]
            }, {"_id": 0})
=======
            # Try to find user by wallet address
            user = await self.db.users.find_one({"wallet_address": sender})
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
            
            if not user:
                logger.warning(f"⚠️  Payment from unknown user: {sender}")
                # Create pending deposit
                await self.db.deposits.insert_one({
                    "tx_hash": tx_hash,
                    "sender": sender,
<<<<<<< HEAD
                    "sender_raw": sender_raw,
=======
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
                    "amount_ton": amount_ton,
                    "status": "pending_user",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "memo": memo
                })
                return
<<<<<<< HEAD

            # Use canonical addresses from DB for balance updates / logs
            user_wallet_address = user.get("wallet_address") or sender
            user_raw_address = user.get("raw_address") or sender_raw
            
            # Credit internal balance
            await self.db.users.update_one(
                {"$or": [{"wallet_address": user_wallet_address}, {"raw_address": user_raw_address}]},
=======
            
            # Credit internal balance
            await self.db.users.update_one(
                {"wallet_address": sender},
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
                {
                    "$inc": {
                        "balance_game": amount_ton,
                        "total_deposited": amount_ton
                    }
                }
            )
            
            # Record deposit
            await self.db.deposits.insert_one({
                "tx_hash": tx_hash,
                "user_id": user["id"],
<<<<<<< HEAD
                "wallet_address": user_wallet_address,
                "raw_address": user_raw_address,
=======
                "wallet_address": sender,
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
                "amount_ton": amount_ton,
                "status": "completed",
                "credited_at": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "memo": memo
            })
            
            # Update stats
            await self.db.admin_stats.update_one(
                {"type": "treasury"},
                {
                    "$inc": {
                        "total_deposits": amount_ton,
                        "deposits_count": 1
                    }
                },
                upsert=True
            )
            
<<<<<<< HEAD
            logger.info(f"✅ Credited {amount_ton} TON to {user_wallet_address[:8]}...")
=======
            logger.info(f"✅ Credited {amount_ton} TON to {sender[:8]}...")
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e
            logger.info(f"   TX: {tx_hash}")
            
        except Exception as e:
            logger.error(f"❌ Error processing payment: {e}")
    
    async def start_monitoring(self):
        """Start monitoring loop"""
        self.is_running = True
        logger.info("🚀 TON Payment Monitor started")
        
        while self.is_running:
            try:
                await self.check_incoming_transactions()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def stop_monitoring(self):
        """Stop monitoring loop"""
        self.is_running = False
        logger.info("🛑 TON Payment Monitor stopped")


# Global monitor instance
payment_monitor = None

async def init_payment_monitor(db):
    """Initialize payment monitor"""
    global payment_monitor
    payment_monitor = TONPaymentMonitor(db)
    # Start in background
    asyncio.create_task(payment_monitor.start_monitoring())
    logger.info("✅ Payment monitor initialized")

async def stop_payment_monitor():
    """Stop payment monitor"""
    global payment_monitor
    if payment_monitor:
        await payment_monitor.stop_monitoring()
