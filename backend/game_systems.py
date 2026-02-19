"""
TON Island Game Systems - Core Business Logic
Implements: Patronage, Upgrades, Durability, Warehouses, Banking
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import uuid

from business_config import (
    BUSINESSES, TIER_TAXES, PATRON_BONUSES, RESOURCE_WEIGHTS,
    WAREHOUSE_CONFIG, PATRON_TAX_RATE, INSTANT_WITHDRAWAL_FEE,
    UPGRADE_MULTIPLIER, calculate_upgrade_cost, calculate_production,
    calculate_income, calculate_repair_cost, get_daily_wear, 
    get_storage_capacity, get_patron_bonus
)

# ==================== PATRONAGE SYSTEM ====================

class PatronageSystem:
    """Handles patron-vassal relationships and bonuses"""
    
    PATRON_CHANGE_COOLDOWN_DAYS = 7
    
    @staticmethod
    def can_be_patron(business_type: str) -> bool:
        """Check if business type can be a patron"""
        config = BUSINESSES.get(business_type, {})
        return config.get("is_patron", False)
    
    @staticmethod
    def get_patron_type(business_type: str) -> Optional[str]:
        """Get patron type for a business"""
        config = BUSINESSES.get(business_type, {})
        return config.get("patron_type")
    
    @staticmethod
    def can_change_patron(last_change: Optional[str]) -> Tuple[bool, int]:
        """Check if patron can be changed (7-day cooldown)"""
        if not last_change:
            return True, 0
        
        try:
            last_dt = datetime.fromisoformat(last_change.replace('Z', '+00:00'))
            cooldown_end = last_dt + timedelta(days=PatronageSystem.PATRON_CHANGE_COOLDOWN_DAYS)
            now = datetime.now(timezone.utc)
            
            if now >= cooldown_end:
                return True, 0
            
            remaining = (cooldown_end - now).days
            return False, remaining
        except (ValueError, TypeError):
            return True, 0
    
    @staticmethod
    def calculate_patron_tax(income: float) -> float:
        """Calculate 1% patron tax from income"""
        return round(income * PATRON_TAX_RATE, 6)
    
    @staticmethod
    def get_patron_bonus_multiplier(patron_type: str, patron_level: int, bonus_type: str) -> float:
        """Get bonus multiplier from patron"""
        return get_patron_bonus(patron_type, patron_level, bonus_type)


# ==================== BUSINESS ECONOMICS ====================

class BusinessEconomics:
    """Handles business upgrades, durability, and production"""
    
    MAX_LEVEL = 10
    DURABILITY_HALT_THRESHOLD = 0  # Production stops at 0%
    
    @staticmethod
    def can_upgrade(business: dict) -> Tuple[bool, Optional[dict]]:
        """Check if business can be upgraded and return cost"""
        current_level = business.get("level", 1)
        
        if current_level >= BusinessEconomics.MAX_LEVEL:
            return False, None
        
        business_type = business.get("business_type")
        cost = calculate_upgrade_cost(business_type, current_level)
        
        return True, cost
    
    @staticmethod
    def upgrade_business(business: dict) -> dict:
        """Apply upgrade to business"""
        new_level = min(business.get("level", 1) + 1, BusinessEconomics.MAX_LEVEL)
        business_type = business.get("business_type")
        
        return {
            "level": new_level,
            "storage.capacity": get_storage_capacity(business_type, new_level),
            "upgraded_at": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def apply_daily_wear(business: dict) -> dict:
        """Calculate and apply daily durability wear"""
        business_type = business.get("business_type")
        level = business.get("level", 1)
        current_durability = business.get("durability", 100)
        
        wear_rate = get_daily_wear(business_type, level)
        
        # Calculate hours since last wear update
        last_update = business.get("last_wear_update")
        if last_update:
            try:
                last_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                hours_passed = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                # Apply wear proportionally to time passed (daily_wear / 24 hours)
                wear = wear_rate * 100 * (hours_passed / 24)
            except (ValueError, TypeError):
                wear = 0
        else:
            wear = 0
        
        new_durability = max(0, current_durability - wear)
        
        return {
            "durability": round(new_durability, 2),
            "last_wear_update": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def get_repair_cost(business: dict) -> dict:
        """Get cost to fully repair business"""
        business_type = business.get("business_type")
        level = business.get("level", 1)
        current_durability = business.get("durability", 100)
        
        # Base repair cost (10% of daily income to repair to 100%)
        base_repair = calculate_repair_cost(business_type, level)
        
        # Scale by missing durability
        missing = 100 - current_durability
        repair_cost = base_repair * (missing / 100)
        
        return {
            "ton_cost": round(repair_cost, 4),
            "current_durability": current_durability,
            "restored_to": 100
        }
    
    @staticmethod
    def is_producing(business: dict) -> bool:
        """Check if business is producing (durability > 0)"""
        return business.get("durability", 100) > BusinessEconomics.DURABILITY_HALT_THRESHOLD
    
    @staticmethod
    def calculate_effective_production(business: dict, patron_bonus: float = 1.0) -> dict:
        """Calculate production with all modifiers"""
        business_type = business.get("business_type")
        level = business.get("level", 1)
        durability = business.get("durability", 100)
        
        if durability <= 0:
            return {
                "production": 0,
                "income_per_hour": 0,
                "status": "halted",
                "reason": "durability_zero"
            }
        
        production = calculate_production(business_type, level, durability, patron_bonus)
        income = calculate_income(business_type, level, durability, patron_bonus)
        
        config = BUSINESSES.get(business_type, {})
        tier_tax = TIER_TAXES.get(config.get("tier", 1), 0.15)
        
        return {
            "production": round(production, 2),
            "income_per_hour": round(income, 6),
            "tax_rate": tier_tax,
            "income_after_tax": round(income * (1 - tier_tax), 6),
            "status": "active" if durability > 20 else "warning",
            "durability": durability
        }


# ==================== WAREHOUSE SYSTEM ====================

class WarehouseSystem:
    """Handles storage limits and P2P warehouse rentals"""
    
    @staticmethod
    def get_total_capacity(business: dict, rented_capacity: int = 0) -> int:
        """Get total storage capacity including rented space"""
        built_in = business.get("storage", {}).get("capacity", 0)
        return built_in + rented_capacity
    
    @staticmethod
    def check_storage_space(business: dict, resource_type: str, amount: float) -> Tuple[bool, int]:
        """Check if there's enough storage space"""
        capacity = business.get("storage", {}).get("capacity", 0)
        current_items = business.get("storage", {}).get("items", {})
        
        weight = RESOURCE_WEIGHTS.get(resource_type, 1)
        weighted_amount = amount * weight
        
        current_used = sum(
            qty * RESOURCE_WEIGHTS.get(res, 1) 
            for res, qty in current_items.items()
        )
        
        available = capacity - current_used
        
        return weighted_amount <= available, int(available / weight)
    
    @staticmethod
    def create_rental_offer(owner_id: str, warehouse_id: str, slots: int, price_per_slot: float) -> dict:
        """Create a warehouse rental listing"""
        return {
            "id": str(uuid.uuid4()),
            "owner_id": owner_id,
            "warehouse_id": warehouse_id,
            "slots_available": slots,
            "price_per_slot_per_day": price_per_slot,
            "total_price_per_day": round(slots * price_per_slot, 4),
            "status": "available",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def calculate_rental_cost(slots: int, price_per_slot: float, days: int) -> dict:
        """Calculate total rental cost with tax"""
        base_cost = slots * price_per_slot * days
        tax = base_cost * WAREHOUSE_CONFIG["rental_tax_rate"]
        
        return {
            "base_cost": round(base_cost, 4),
            "tax": round(tax, 4),
            "total": round(base_cost + tax, 4),
            "days": days,
            "slots": slots
        }


# ==================== BANKING & WITHDRAWAL ====================

class BankingSystem:
    """Handles dual-queue withdrawals and instant withdrawal via banks"""
    
    STANDARD_QUEUE_HOURS = 24
    INSTANT_FEE = 0.01  # 1% to bank owner
    
    @staticmethod
    def create_withdrawal_request(user_wallet: str, amount: float, withdrawal_type: str = "standard") -> dict:
        """Create a withdrawal request"""
        commission = 0.03  # Platform commission
        net_amount = amount * (1 - commission)
        
        if withdrawal_type == "instant":
            bank_fee = amount * BankingSystem.INSTANT_FEE
            net_amount -= bank_fee
        else:
            bank_fee = 0
        
        scheduled_for = datetime.now(timezone.utc)
        if withdrawal_type == "standard":
            scheduled_for += timedelta(hours=BankingSystem.STANDARD_QUEUE_HOURS)
        
        return {
            "id": str(uuid.uuid4()),
            "user_wallet": user_wallet,
            "amount": amount,
            "withdrawal_type": withdrawal_type,  # "standard" or "instant"
            "platform_commission": round(amount * commission, 6),
            "bank_fee": round(bank_fee, 6),
            "net_amount": round(net_amount, 6),
            "status": "pending",
            "scheduled_for": scheduled_for.isoformat(),
            "bank_id": None,  # Will be set for instant withdrawals
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def can_process_instant(bank_business: dict, withdrawal_amount: float) -> Tuple[bool, str]:
        """Check if bank can process instant withdrawal"""
        if not bank_business:
            return False, "no_bank_selected"
        
        config = BUSINESSES.get(bank_business.get("business_type"), {})
        if not config.get("instant_withdrawal"):
            return False, "not_a_bank"
        
        # Bank must have durability > 50%
        if bank_business.get("durability", 0) < 50:
            return False, "bank_durability_low"
        
        return True, "ok"
    
    @staticmethod
    def get_available_banks(banks_list: List[dict]) -> List[dict]:
        """Filter banks that can process instant withdrawals"""
        available = []
        for bank in banks_list:
            can_process, _ = BankingSystem.can_process_instant(bank, 0)
            if can_process:
                available.append({
                    "id": bank.get("id"),
                    "owner": bank.get("owner"),
                    "owner_username": bank.get("owner_username"),
                    "level": bank.get("level", 1),
                    "durability": bank.get("durability", 100),
                    "fee_rate": BankingSystem.INSTANT_FEE
                })
        return available


# ==================== TAX SYSTEM ====================

class TaxSystem:
    """Three-way tax distribution: Treasury, Patron, Player"""
    
    @staticmethod
    def calculate_tax_split(gross_income: float, tier: int, has_patron: bool) -> dict:
        """Calculate how income is split between treasury, patron, and player"""
        tier_tax_rate = TIER_TAXES.get(tier, 0.15)
        
        # Tier tax goes to treasury
        treasury_tax = gross_income * tier_tax_rate
        
        # After treasury tax
        after_treasury = gross_income - treasury_tax
        
        # Patron tax (1% of remaining)
        patron_tax = after_treasury * PATRON_TAX_RATE if has_patron else 0
        
        # Player receives the rest
        player_income = after_treasury - patron_tax
        
        return {
            "gross": round(gross_income, 6),
            "treasury_tax": round(treasury_tax, 6),
            "treasury_rate": tier_tax_rate,
            "patron_tax": round(patron_tax, 6),
            "patron_rate": PATRON_TAX_RATE if has_patron else 0,
            "player_income": round(player_income, 6),
            "effective_rate": round((treasury_tax + patron_tax) / gross_income, 4) if gross_income > 0 else 0
        }
    
    @staticmethod
    def apply_taxes(gross_income: float, business: dict, patron_wallet: Optional[str] = None) -> dict:
        """Apply all taxes and return distribution"""
        config = BUSINESSES.get(business.get("business_type"), {})
        tier = config.get("tier", 1)
        has_patron = patron_wallet is not None
        
        split = TaxSystem.calculate_tax_split(gross_income, tier, has_patron)
        
        return {
            **split,
            "patron_wallet": patron_wallet,
            "distributions": [
                {"to": "treasury", "amount": split["treasury_tax"]},
                {"to": patron_wallet, "amount": split["patron_tax"]} if has_patron else None,
                {"to": "player", "amount": split["player_income"]}
            ]
        }


# ==================== INCOME COLLECTION ====================

class IncomeCollector:
    """Handles periodic income collection from businesses"""
    
    @staticmethod
    def calculate_pending_income(business: dict, patron_bonus: float = 1.0) -> dict:
        """Calculate income accumulated since last collection"""
        last_collection = business.get("last_collection")
        
        if not last_collection:
            return {"pending": 0, "hours": 0}
        
        try:
            last_dt = datetime.fromisoformat(last_collection.replace('Z', '+00:00'))
            hours_passed = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
        except (ValueError, TypeError):
            hours_passed = 0
        
        # Get current production status
        production = BusinessEconomics.calculate_effective_production(business, patron_bonus)
        
        if production["status"] == "halted":
            return {"pending": 0, "hours": hours_passed, "halted": True}
        
        income = production["income_after_tax"] * hours_passed
        
        return {
            "pending": round(income, 6),
            "hours": round(hours_passed, 2),
            "halted": False
        }
    
    @staticmethod
    def collect_income(business: dict, patron_wallet: Optional[str] = None) -> dict:
        """Collect all pending income with tax distribution"""
        pending = IncomeCollector.calculate_pending_income(business)
        
        if pending["halted"]:
            return {
                "collected": 0,
                "halted": True,
                "message": "Production halted - repair needed"
            }
        
        gross = pending["pending"]
        
        # Apply tax split
        tax_info = TaxSystem.apply_taxes(gross, business, patron_wallet)
        
        return {
            "collected": gross,
            "hours": pending["hours"],
            "player_receives": tax_info["player_income"],
            "treasury_receives": tax_info["treasury_tax"],
            "patron_receives": tax_info["patron_tax"],
            "patron_wallet": patron_wallet,
            "collected_at": datetime.now(timezone.utc).isoformat()
        }
