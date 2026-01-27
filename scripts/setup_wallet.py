#!/usr/bin/env python3
"""
Настройка кошелька для приёма депозитов
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def setup_wallet():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    print("=== Настройка кошелька для депозитов ===\n")
    print("Введите адрес TON кошелька для приёма депозитов:")
    print("(Пример: EQYourWalletAddress123...)")
    
    receiver_address = input("\nАдрес кошелька: ").strip()
    
    if not receiver_address:
        print("❌ Адрес не может быть пустым!")
        return
    
    print("\nВыберите сеть:")
    print("1. testnet (для тестирования)")
    print("2. mainnet (для продакшена)")
    network_choice = input("\nВыбор (1/2): ").strip()
    
    network = "testnet" if network_choice == "1" else "mainnet"
    
    # Обновить или создать настройки
    result = await db.game_settings.update_one(
        {"type": "ton_wallet"},
        {"$set": {
            "type": "ton_wallet",
            "network": network,
            "receiver_address": receiver_address,
            "updated_at": asyncio.get_event_loop().time()
        }},
        upsert=True
    )
    
    if result.modified_count > 0 or result.upserted_id:
        print(f"\n✅ Кошелёк настроен успешно!")
        print(f"   Сеть: {network}")
        print(f"   Адрес: {receiver_address}")
        print(f"\nТеперь пользователи могут пополнять баланс!")
    else:
        print("⚠️ Не удалось обновить настройки")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(setup_wallet())
