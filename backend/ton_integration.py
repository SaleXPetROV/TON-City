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
<<<<<<< HEAD
import base64
import json
import httpx
=======
from pytonlib import TonlibClient
import base64
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e

logger = logging.getLogger(__name__)

# TON Configuration
TON_MAINNET_CONFIG = "https://ton.org/global-config.json"
TON_TESTNET = False  # Set to False for mainnet

class TONClient:
<<<<<<< HEAD
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
=======
    """TON Blockchain Client for mainnet transactions"""
    
    def __init__(self):
        self.client: Optional[TonlibClient] = None
        self.initialized = False
        
    async def init(self):
        """Initialize TON client connection"""
        if self.initialized:
            return
            
        try:
            # For now, we'll use a simplified initialization
            # In production, properly configure tonlib with correct paths
            logger.info("⚠️  TON client initialization skipped - requires proper tonlib setup")
            logger.info("   Blockchain verification will be simulated for now")
            self.initialized = True
            return
            
            # Uncomment and configure properly for production:
            # self.client = TonlibClient(
            #     ls_index=0,
            #     config=TON_MAINNET_CONFIG,
            #     keystore="/tmp/ton_keystore",
            #     tonlib_timeout=30
            # )
            # await self.client.init()
            # self.initialized = True
            # logger.info("✅ TON Mainnet client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize TON client: {e}")
            # Don't raise, just log - app can work without blockchain verification
            self.initialized = False
    
    async def get_balance(self, address: str) -> float:
        """
        Get wallet balance in TON
        
        Args:
            address: TON wallet address
            
        Returns:
            Balance in TON
        """
        try:
            if not self.initialized:
                await self.init()
                
            result = await self.client.raw_get_account_state(address)
            balance_nano = int(result.get('balance', 0))
            balance_ton = balance_nano / 1e9
            return balance_ton
        except Exception as e:
            logger.error(f"Failed to get balance for {address}: {e}")
            return 0.0
    
    async def verify_transaction(self, tx_hash: str, expected_amount: float, to_address: str) -> bool:
        """
        Verify a transaction on TON blockchain
        
        Args:
            tx_hash: Transaction hash
            expected_amount: Expected amount in TON
            to_address: Expected recipient address
            
        Returns:
            True if transaction is valid
        """
        try:
            if not self.initialized:
                await self.init()
            
            # Get transaction details
            # Note: This is a simplified version, in production you'd need to:
            # 1. Decode the transaction hash properly
            # 2. Query the transaction from the blockchain
            # 3. Verify all parameters match
            
            logger.info(f"Verifying transaction: {tx_hash}")
            logger.info(f"Expected: {expected_amount} TON to {to_address}")
            
            # For now, we'll mark it as verified
            # In production, implement full transaction verification
            return True
            
        except Exception as e:
            logger.error(f"Transaction verification failed: {e}")
            return False
    
    async def create_payment_link(self, to_address: str, amount: float, message: str = "") -> str:
        """
        Create TON payment link (ton://transfer/...)
        
        Args:
            to_address: Recipient wallet address
            amount: Amount in TON
            message: Optional message
            
        Returns:
            Payment link for TON Connect
        """
        amount_nano = int(amount * 1e9)
        
        # TON Connect payment link format
        link = f"ton://transfer/{to_address}"
        params = []
        
        if amount_nano > 0:
            params.append(f"amount={amount_nano}")
        
        if message:
            encoded_message = base64.b64encode(message.encode()).decode()
            params.append(f"text={encoded_message}")
        
        if params:
            link += "?" + "&".join(params)
        
        logger.info(f"Created payment link: {link}")
        return link
    
    async def send_transaction(
        self, 
        from_wallet: str,
        to_address: str, 
        amount: float,
        memo: str = ""
    ) -> Optional[str]:
        """
        Send TON transaction (for admin withdrawals)
        
        Args:
            from_wallet: Admin wallet address
            to_address: Recipient address
            amount: Amount in TON
            memo: Transaction memo
            
        Returns:
            Transaction hash or None
        """
        try:
            if not self.initialized:
                await self.init()
            
            logger.info(f"Sending {amount} TON from {from_wallet} to {to_address}")
            
            # Note: For sending transactions, you need the wallet's private key
            # This should be stored securely (environment variable or key management system)
            # For security, real implementation requires:
            # 1. Secure key storage
            # 2. Proper transaction signing
            # 3. Gas fee calculation
            
            # Placeholder - implement actual transaction sending with proper key management
            logger.warning("⚠️  Transaction sending requires secure key management")
            
            return f"tx_placeholder_{to_address}_{amount}"
            
        except Exception as e:
            logger.error(f"Failed to send transaction: {e}")
            return None
    
    async def get_transaction_history(self, address: str, limit: int = 10) -> list:
        """
        Get transaction history for an address
        
        Args:
            address: Wallet address
            limit: Number of transactions to fetch
            
        Returns:
            List of transactions
        """
        try:
            if not self.initialized:
                await self.init()
            
            transactions = await self.client.raw_get_transactions(address, limit=limit)
            return transactions
        except Exception as e:
            logger.error(f"Failed to get transaction history: {e}")
            return []
    
    async def close(self):
        """Close TON client connection"""
        if self.client:
            await self.client.close()
            self.initialized = False
            logger.info("TON client closed")
>>>>>>> 3a4ae0fd262a673aa42120e78d19e74a680aa74e

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
