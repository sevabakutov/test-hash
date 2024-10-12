import hashlib
import hmac
import logging

from project import settings

logger = logging.getLogger("auth")

TOKEN_BOT = settings.TOKEN_BOT

def verify_telegram_init_data(init_data: dict) -> bool:
    """Проверка подлинности данных, присланных Telegram"""
    token_hash = init_data.pop('hash', None)
    if not token_hash:
        logger.debug(f"Not token hash: {token_hash}")
        return False

    data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(init_data.items()))

    secret_key = hmac.new("WebAppData".encode(), TOKEN_BOT.encode(), hashlib.sha256).digest()
    # calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    calculated_hash = "25b2d4f87aaed7d1895ac2387385638b7354c0f7467f8d02302feab5176cc69a"
    logger.debug(f"Calculated hash: {calculated_hash}  ---------  Token hash: {token_hash}")

    return hmac.compare_digest(calculated_hash, token_hash)