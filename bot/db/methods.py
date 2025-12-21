import hashlib
from enum import Enum
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, select, update, delete, exists

from db.models import VPNUsers, Payments, PromoCode, UserPromoCode, UserMessages, Referrals, ReferralRewards
import glv

class PaymentPlatform(Enum):
    YOOKASSA = 0
    CRYPTOMUS = 1
    TELEGRAM = 2

engine = create_async_engine(glv.config['DB_URL'])

async def create_vpn_user(tg_id: int):
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.tg_id == tg_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
        if result is not None:
            return
        hash = hashlib.md5(str(tg_id).encode()).hexdigest()
        sql_query = insert(VPNUsers).values(tg_id=tg_id, vpn_id=hash, test=None)
        await conn.execute(sql_query)
        await conn.commit()

async def get_vpn_user(tg_id: int) -> VPNUsers:
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.tg_id == tg_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
    return result

async def get_marzban_profile_by_vpn_id(vpn_id: str):
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.vpn_id == vpn_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
    return result

async def update_vpn_id(tg_id: int, vpn_id: str):
    async with engine.connect() as conn:
        sql_q = update(VPNUsers).where(VPNUsers.tg_id == tg_id).values(vpn_id=vpn_id)
        await conn.execute(sql_q)
        await conn.commit()

async def get_vpn_user_by_vpn_id(vpn_id: str) -> VPNUsers:
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.vpn_id == vpn_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
    return result

async def is_trial_available(tg_id: int) -> bool:
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.tg_id == tg_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
    return result.test is None

async def start_trial(tg_id):
    async with engine.connect() as conn:
        sql_q = update(VPNUsers).where(VPNUsers.tg_id == tg_id).values(test=True)
        await conn.execute(sql_q)
        await conn.commit()

async def disable_trial(tg_id):
    async with engine.connect() as conn:
        sql_q = update(VPNUsers).where(VPNUsers.tg_id == tg_id).values(test=False)
        await conn.execute(sql_q)
        await conn.commit()

async def is_test_subscription(tg_id: int) -> bool:
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.tg_id == tg_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
    return result.test

async def add_payment(tg_id: int, callback: str, lang_code: str, payment_id:str, platform:PaymentPlatform, confirmed: bool = False, message_id: int = None, from_notification: bool = False) -> dict:
    async with engine.connect() as conn:
        sql_q = insert(Payments).values(tg_id=tg_id, payment_id=payment_id, callback=callback, lang=lang_code, type=platform.value, confirmed=confirmed, created_at=datetime.now(), message_id=message_id, from_notification=from_notification)
        await conn.execute(sql_q)
        await conn.commit()

async def get_payment(payment_id, platform:PaymentPlatform) -> Payments:
    async with engine.connect() as conn:
        sql_q = select(Payments).where(
            Payments.payment_id == payment_id,
            Payments.type == platform.value
        )
        payment: Payments = (await conn.execute(sql_q)).fetchone()
    return payment

async def confirm_payment(payment_id):
    async with engine.connect() as conn:
        sql_q = update(Payments).where(Payments.payment_id == payment_id).values(confirmed=True)
        await conn.execute(sql_q)
        await conn.commit()

async def delete_payment(payment_id):
    async with engine.connect() as conn:
        sql_q = delete(Payments).where(Payments.payment_id == payment_id)
        await conn.execute(sql_q)
        await conn.commit()

async def get_promo_code_by_code(code: str) -> PromoCode:
    async with engine.connect() as conn:
        sql_query = select(PromoCode).where(PromoCode.code == code.upper())
        result: PromoCode = (await conn.execute(sql_query)).fetchone()
    return result

async def has_activated_promo_code(tg_id: int, promo_code_id: int) -> bool:
    async with engine.connect() as conn:
        sql_query = select(UserPromoCode).where(UserPromoCode.tg_id == tg_id, UserPromoCode.promo_code_id == promo_code_id)
        result = (await conn.execute(sql_query)).fetchone()
    return result is not None

async def activate_promo_code(tg_id: int, promo_code_id: int):
    async with engine.connect() as conn:
        sql_query = insert(UserPromoCode).values(tg_id=tg_id, promo_code_id=promo_code_id, activated_at=datetime.now())
        await conn.execute(sql_query)
        await conn.commit()

async def get_user_promo_discount(tg_id: int) -> float:
    async with engine.connect() as conn:
        sql_query = select(PromoCode.discount_percent).join(
            UserPromoCode, PromoCode.id == UserPromoCode.promo_code_id
        ).where(
            UserPromoCode.tg_id == tg_id,
            UserPromoCode.used == False,
            PromoCode.expires_at > datetime.now()
        )
        result = (await conn.execute(sql_query)).fetchone()
    return result[0] if result else 0.0

async def has_confirmed_payments(tg_id: int) -> bool:
    async with engine.connect() as conn:
        sql_query = select(exists().where(
            Payments.tg_id == tg_id, 
            Payments.confirmed == True
        ))
        result = (await conn.execute(sql_query)).scalar()
    return result

async def use_all_promo_codes(tg_id: int):
    async with engine.connect() as conn:
        sql_query = update(UserPromoCode).where(UserPromoCode.tg_id == tg_id).values(used=True)
        await conn.execute(sql_query)
        await conn.commit()

async def get_vpn_users():
    async with engine.connect() as conn:
        sql_query = select(VPNUsers)
        result: list[VPNUsers] = (await conn.execute(sql_query)).fetchall()
    return result

async def get_active_promo_codes():
    async with engine.connect() as conn:
        sql_query = select(PromoCode).where(
            PromoCode.expires_at > datetime.now()
        ).order_by(PromoCode.created_at.desc())
        result: list[PromoCode] = (await conn.execute(sql_query)).fetchall()
    return result

async def add_promo_code(code: str, discount_percent: int, expires_at: datetime = None):
    async with engine.connect() as conn:
        sql_query = insert(PromoCode).values(
            code=code.upper(),
            discount_percent=discount_percent,
            expires_at=expires_at,
            created_at=datetime.now()
        )
        await conn.execute(sql_query)
        await conn.commit()

async def delete_promo_code(promo_code_id: int):
    async with engine.connect() as conn:
        sql_query = delete(PromoCode).where(PromoCode.id == promo_code_id)
        await conn.execute(sql_query)
        await conn.commit()

async def get_promo_code_by_id(promo_code_id: int) -> PromoCode:
    async with engine.connect() as conn:
        sql_query = select(PromoCode).where(PromoCode.id == promo_code_id)
        result: PromoCode = (await conn.execute(sql_query)).fetchone()
    return result

async def save_user_message(tg_id: int, message_id: int, message_type: str):
    async with engine.connect() as conn:
        check_query = select(UserMessages).where(
            UserMessages.tg_id == tg_id,
            UserMessages.message_id == message_id,
            UserMessages.message_type == message_type
        )
        existing = (await conn.execute(check_query)).fetchone()
        
        if not existing:
            sql_query = insert(UserMessages).values(
                tg_id=tg_id,
                message_id=message_id,
                message_type=message_type,
                created_at=datetime.now()
            )
            await conn.execute(sql_query)
            await conn.commit()

async def get_user_messages(tg_id: int) -> dict:
    async with engine.connect() as conn:
        sql_query = select(UserMessages).where(
            UserMessages.tg_id == tg_id
        ).order_by(UserMessages.created_at.asc())
        results = (await conn.execute(sql_query)).fetchall()
    
    messages = {
        'navigation': [],
        'profile': None,
        'payment': None,
        'notification': [],
        'success': None,
        'important': None
    }
    
    seen_single = set()
    
    for row in results:
        msg_type = row.message_type
        msg_id = row.message_id
        
        if msg_type in ['navigation', 'notification']:
            if msg_id not in messages[msg_type]:
                messages[msg_type].append(msg_id)
        else:
            if msg_type not in seen_single:
                messages[msg_type] = msg_id
                seen_single.add(msg_type)
    
    return messages

async def delete_user_message(tg_id: int, message_id: int, message_type: str):
    async with engine.connect() as conn:
        sql_query = delete(UserMessages).where(
            UserMessages.tg_id == tg_id,
            UserMessages.message_id == message_id,
            UserMessages.message_type == message_type
        )
        await conn.execute(sql_query)
        await conn.commit()

async def clear_user_messages_by_type(tg_id: int, message_types: list):
    async with engine.connect() as conn:
        sql_query = delete(UserMessages).where(
            UserMessages.tg_id == tg_id,
            UserMessages.message_type.in_(message_types)
        )
        await conn.execute(sql_query)
        await conn.commit()

async def clear_user_messages(tg_id: int):
    async with engine.connect() as conn:
        sql_query = delete(UserMessages).where(UserMessages.tg_id == tg_id)
        await conn.execute(sql_query)
        await conn.commit()

async def cleanup_old_messages(days: int = 7):
    cutoff_date = datetime.now() - timedelta(days=days)
    async with engine.connect() as conn:
        sql_query = delete(UserMessages).where(UserMessages.created_at < cutoff_date)
        await conn.execute(sql_query)
        await conn.commit()

async def create_referral(referrer_id: int, referred_id: int):
    if referrer_id == referred_id:
        return
    async with engine.connect() as conn:
        check_query = select(Referrals).where(Referrals.referred_id == referred_id)
        existing = (await conn.execute(check_query)).fetchone()
        if existing:
            return
        referrer_exists = select(VPNUsers).where(VPNUsers.tg_id == referrer_id)
        referrer_check = (await conn.execute(referrer_exists)).fetchone()
        if not referrer_check:
            return
        try:
            sql_query = insert(Referrals).values(
                referrer_id=referrer_id,
                referred_id=referred_id,
                created_at=datetime.now()
            )
            await conn.execute(sql_query)
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise

async def get_referrer_id(referred_id: int):
    async with engine.connect() as conn:
        sql_query = select(Referrals.referrer_id).where(Referrals.referred_id == referred_id)
        result = (await conn.execute(sql_query)).fetchone()
    return result[0] if result else None

async def get_referral_count(referrer_id: int) -> int:
    async with engine.connect() as conn:
        sql_query = select(Referrals).where(Referrals.referrer_id == referrer_id)
        results = (await conn.execute(sql_query)).fetchall()
    return len(results)

async def get_referrals_with_payments(referrer_id: int) -> int:
    async with engine.connect() as conn:
        sql_query = select(Referrals.referred_id).where(Referrals.referrer_id == referrer_id)
        referral_ids = (await conn.execute(sql_query)).fetchall()
        if not referral_ids:
            return 0
        referred_ids = [row[0] for row in referral_ids]
        count_query = select(Payments.tg_id).where(
            Payments.tg_id.in_(referred_ids),
            Payments.confirmed == True
        ).distinct()
        results = (await conn.execute(count_query)).fetchall()
    return len(results)

async def get_total_referral_rewards(referrer_id: int) -> int:
    async with engine.connect() as conn:
        sql_query = select(ReferralRewards.reward_amount).where(ReferralRewards.referrer_id == referrer_id)
        results = (await conn.execute(sql_query)).fetchall()
    return sum(row[0] for row in results) if results else 0

async def add_referral_reward(referrer_id: int, referred_id: int, payment_id: str, reward_amount: int, reward_type: str):
    if not payment_id or not reward_amount or reward_amount <= 0:
        return
    async with engine.connect() as conn:
        check_query = select(ReferralRewards).where(
            ReferralRewards.referrer_id == referrer_id,
            ReferralRewards.payment_id == payment_id
        )
        existing = (await conn.execute(check_query)).fetchone()
        if existing:
            return
        try:
            sql_query = insert(ReferralRewards).values(
                referrer_id=referrer_id,
                referred_id=referred_id,
                payment_id=payment_id,
                reward_amount=reward_amount,
                reward_type=reward_type,
                created_at=datetime.now()
            )
            await conn.execute(sql_query)
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise

def generate_referral_code(tg_id: int) -> str:
    import base64
    encoded = base64.urlsafe_b64encode(str(tg_id).encode()).decode().rstrip('=')
    return f"ref_{encoded}"

def decode_referral_code(code: str) -> int:
    import base64
    try:
        if not code.startswith("ref_"):
            return None
        encoded = code.replace("ref_", "")
        padding = 4 - (len(encoded) % 4)
        if padding != 4:
            encoded += '=' * padding
        decoded = base64.urlsafe_b64decode(encoded).decode()
        return int(decoded)
    except Exception:
        return None