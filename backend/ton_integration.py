"""
TON Blockchain Integration Module
Handles real TON mainnet transactions
"""
import os
import asyncio
import logging
from typing import Optional, Dict
from tonsdk.contract.wallet import WalletVersionEnum, Wallets
from tonsdk.utils import bytes_to_b64str, to_nano
import base64
import json
import httpx

logger = logging.getLogger(__name__)

# TON Configuration
TON_MAINNET_CONFIG = "https://ton.org/global-config.json"
TON_TESTNET = False  # Set to False for mainnet

class TONClient:
    def __init__(self):
        self.initialized = False
        
    async def init(self):
        if self.initialized: return
        try:
            # Инициализация клиента (для работы send_ton_payout)
            self.initialized = True
            logger.info("✅ TON Client initialized for transfers")
        except Exception as e:
            logger.error(f"❌ Failed to init: {e}")

    async def send_ton_payout(self, dest_address: str, amount_ton: float, mnemonics: str):
        """Отправка TON через API Toncenter с проверкой адреса"""
        try:
            api_key = os.environ.get("TONCENTER_API_KEY") or ""
            toncenter_endpoint = os.environ.get("TONCENTER_API_ENDPOINT", "https://toncenter.com/api/v2").rstrip('/')
            
            # 1. Инициализация через точные имена из твоей библиотеки
            from tonsdk.crypto import mnemonic_to_wallet_key
            # Импортируем оба возможных варианта
            from tonsdk.contract.wallet import WalletV4ContractR2, WalletV3ContractR2
            
            mnemonics_list = mnemonics.split()
            pub_k, priv_k = mnemonic_to_wallet_key(mnemonics_list)
            
            # --- ПОПРОБУЕМ V4 (самый частый вариант) ---
            _wallet = WalletV4ContractR2(public_key=pub_k, private_key=priv_k, workchain=0)
            
            # 2. ПРОВЕРКА АДРЕСА
            wallet_address = _wallet.address.to_string(True, True, False)
            logger.info(f"📢 Скрипт инициализировал адрес (V4R2): {wallet_address}")
            
            # ВАЖНО: Сравни этот адрес с Tonkeeper. 
            # Если они РАЗНЫЕ, раскомментируй строку ниже, а верхнюю удали:
            # _wallet = WalletV3ContractR2(public_key=pub_k, private_key=priv_k, workchain=0)
            
            # 3. Получаем актуальный SEQNO
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {"address": wallet_address}
                headers = {"X-API-Key": api_key} if api_key else {}
                
                resp = await client.get(f"{toncenter_endpoint}/getWalletInformation", params=params, headers=headers)
                if resp.status_code != 200:
                    raise Exception(f"Toncenter error {resp.status_code}")
                
                data = resp.json()
                seqno = data.get("result", {}).get("seqno", 0)
                if seqno is None: seqno = 0

            # 4. Создаем сообщение о переводе
            query = _wallet.create_transfer_message(
                to_addr=dest_address,
                amount=to_nano(amount_ton, 'ton'),
                seqno=int(seqno),
                payload=None 
            )

            # 5. Отправляем BOC в сеть
            boc = bytes_to_b64str(query['message'].to_boc(False))
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{toncenter_endpoint}/sendBoc", json={"boc": boc}, headers=headers)
                res_data = resp.json()
                
                if resp.status_code == 200 and res_data.get("ok"):
                    tx_hash = res_data.get("result", {}).get("hash") or "sent_success"
                    logger.info(f"✅ УСПЕХ! Хэш: {tx_hash}")
                    return tx_hash
                else:
                    error_msg = res_data.get("error", "Unknown blockchain error")
                    logger.error(f"❌ Сеть отклонила BOC: {error_msg}")
                    raise Exception(f"Blockchain rejected: {error_msg}")

        except Exception as e:
            logger.error(f"❌ Критическая ошибка в send_ton_payout: {e}")
            raise e

    async def get_transaction_history(self, address: str, limit: int = 20):
        """Получение истории для payment_monitor.py"""
        try:
            import httpx
            # Используем публичное API Toncenter
            url = f"https://toncenter.com/api/v2/getTransactions?address={address}&limit={limit}"
            async with httpx.AsyncClient() as client:
                r = await client.get(url)
                data = r.json()
                return data.get("result", [])
        except Exception as e:
            logger.error(f"Failed to fetch history: {e}")
            return []

    async def check_incoming_transactions(self):
        try:
            settings = await self.get_game_settings()
            receiver_address = settings.get("receiver_address")
            if not receiver_address: return

            # Получаем историю транзакций кошелька проекта
            transactions = await ton_client.get_transaction_history(receiver_address)
            
            for tx in transactions:
                # 1. Проверяем, не обрабатывали ли мы этот tx_hash раньше
                # 2. Ищем в комментарии (payload) ID пользователя
                # 3. Если нашли, вызываем:
                # await self.process_payment(user_id, amount, tx_hash)
                pass
        except Exception as e:
            logger.error(f"Error in monitor: {e}")

# Global TON client instance
ton_client = TONClient()

async def init_ton_client():
    """Initialize TON client on startup"""
    await ton_client.init()

async def close_ton_client():
    """Close TON client on shutdown"""
    await ton_client.close()

# Helper functions
def ton_to_nano(amount: float) -> int:
    """Convert TON to nanoTON"""
    return int(amount * 1e9)

def nano_to_ton(amount: int) -> float:
    """Convert nanoTON to TON"""
    return amount / 1e9

def validate_ton_address(address: str) -> bool:
    """
    Validate TON address format
    
    Args:
        address: TON wallet address
        
    Returns:
        True if valid
    """
    # TON addresses are typically 48 characters
    # Format: EQxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    if not address:
        return False
    
    if len(address) != 48:
        return False
    
    if not address.startswith(('EQ', 'UQ')):
        return False
    
    return True
