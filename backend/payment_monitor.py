"""
TON Payment Monitor
Monitors incoming TON transactions and credits internal balance
"""
import logging
import asyncio
from datetime import datetime, timezone
import os   
from tonsdk.utils import Address

def to_raw(address_str):
    try:
        return Address(address_str).to_string(is_user_friendly=False)
    except Exception:
        return address_str


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
        """Check for new incoming TON transactions"""
        try:
            settings = await self.get_game_settings()
            receiver_address = settings.get("receiver_address")
            
            if not receiver_address:
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
    
    async def process_incoming_payment(self, transaction):
        """
        Process an incoming TON payment
        
        Args:
            transaction: Transaction data from blockchain
        """
        try:
            tx_hash = transaction.get("hash")
            sender = transaction.get("sender")
            sender_raw = transaction.get("sender_raw") or to_raw(sender)
            amount = transaction.get("amount", 0)
            amount_ton = amount / 1_000_000_000  # Convert from nanotons
            
            # Find user by wallet address
            user = await self.db.users.find_one({
                "$or": [
                    {"wallet_address": sender},
                    {"raw_address": sender},
                    {"wallet_address": sender_raw},
                    {"raw_address": sender_raw},
                ]
            })
            
            if not user:
                logger.warning(f"⚠️  Payment from unknown user: {sender}")
                # Create pending deposit
                await self.db.deposits.insert_one({
                    "tx_hash": tx_hash,
                    "sender": sender,
                    "sender_raw": sender_raw,
                    "amount_ton": amount_ton,
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                return
            
            # Check if already processed
            existing = await self.db.deposits.find_one({"tx_hash": tx_hash})
            if existing:
                logger.debug(f"Transaction {tx_hash} already processed")
                return
            
            # Credit user balance
            await self.db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$inc": {
                        "balance_ton": amount_ton,
                        "total_deposited": amount_ton
                    }
                }
            )
            
            # Record deposit
            await self.db.deposits.insert_one({
                "tx_hash": tx_hash,
                "user_id": user.get("id", str(user["_id"])),
                "wallet_address": user.get("wallet_address"),
                "raw_address": user.get("raw_address"),
                "amount_ton": amount_ton,
                "status": "completed",
                "credited_at": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
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
            
            logger.info(f"✅ Credited {amount_ton} TON to {user.get('username', 'User')}")
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
