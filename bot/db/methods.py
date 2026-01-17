import hashlib
from enum import Enum
from datetime import datetime, timedelta
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, select, update, delete, exists
from sqlalchemy.exc import OperationalError

from db.models import VPNUsers, Payments, PromoCode, UserPromoCode, UserMessages, TrafficNotification
import glv

class PaymentPlatform(Enum):
    YOOKASSA = 0
    CRYPTOMUS = 1
    TELEGRAM = 2

engine = create_async_engine(
    glv.config['DB_URL'],
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

async def _retry_on_connection_error(func, max_retries=3, delay=0.5):
    for attempt in range(max_retries):
        try:
            return await func()
        except OperationalError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay * (attempt + 1))

async def create_vpn_user(tg_id: int):
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.tg_id == tg_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
        if result is not None:
            return
    async with engine.begin() as conn:
        hash = hashlib.md5(str(tg_id).encode()).hexdigest()
        sql_query = insert(VPNUsers).values(tg_id=tg_id, vpn_id=hash, test=None)
        await conn.execute(sql_query)

async def get_vpn_user(tg_id: int) -> VPNUsers:
    async def _execute():
        async with engine.connect() as conn:
            sql_query = select(VPNUsers).where(VPNUsers.tg_id == tg_id)
            result: VPNUsers = (await conn.execute(sql_query)).fetchone()
        return result
    
    return await _retry_on_connection_error(_execute)

async def get_marzban_profile_by_vpn_id(vpn_id: str):
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.vpn_id == vpn_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
    return result

async def update_vpn_id(tg_id: int, vpn_id: str):
    async with engine.begin() as conn:
        sql_q = update(VPNUsers).where(VPNUsers.tg_id == tg_id).values(vpn_id=vpn_id)
        await conn.execute(sql_q)

async def get_vpn_user_by_vpn_id(vpn_id: str) -> VPNUsers:
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.vpn_id == vpn_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
    return result

async def is_trial_available(tg_id: int) -> bool:
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.tg_id == tg_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
    if result is None:
        return True
    return result.test is None

async def start_trial(tg_id):
    async with engine.begin() as conn:
        sql_q = update(VPNUsers).where(VPNUsers.tg_id == tg_id).values(test=True)
        await conn.execute(sql_q)

async def disable_trial(tg_id):
    async with engine.begin() as conn:
        sql_q = update(VPNUsers).where(VPNUsers.tg_id == tg_id).values(test=False)
        await conn.execute(sql_q)

async def is_test_subscription(tg_id: int) -> bool:
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.tg_id == tg_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
    if result is None:
        return False
    return result.test

async def add_payment(tg_id: int, callback: str, lang_code: str, payment_id:str, platform:PaymentPlatform, confirmed: bool = False, message_id: int = None, from_notification: bool = False) -> dict:
    async with engine.begin() as conn:
        sql_q = insert(Payments).values(tg_id=tg_id, payment_id=payment_id, callback=callback, lang=lang_code, type=platform.value, confirmed=confirmed, created_at=datetime.now(), message_id=message_id, from_notification=from_notification)
        await conn.execute(sql_q)

async def get_payment(payment_id, platform:PaymentPlatform) -> Payments:
    async with engine.connect() as conn:
        sql_q = select(Payments).where(
            Payments.payment_id == payment_id,
            Payments.type == platform.value
        )
        payment: Payments = (await conn.execute(sql_q)).fetchone()
    return payment

async def confirm_payment(payment_id):
    async with engine.begin() as conn:
        sql_q = update(Payments).where(Payments.payment_id == payment_id).values(confirmed=True)
        await conn.execute(sql_q)

async def delete_payment(payment_id):
    async with engine.begin() as conn:
        sql_q = delete(Payments).where(Payments.payment_id == payment_id)
        await conn.execute(sql_q)

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
    async with engine.begin() as conn:
        sql_query = insert(UserPromoCode).values(tg_id=tg_id, promo_code_id=promo_code_id, activated_at=datetime.now())
        await conn.execute(sql_query)

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
    async with engine.begin() as conn:
        sql_query = update(UserPromoCode).where(UserPromoCode.tg_id == tg_id).values(used=True)
        await conn.execute(sql_query)

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
    async with engine.begin() as conn:
        sql_query = insert(PromoCode).values(
            code=code.upper(),
            discount_percent=discount_percent,
            expires_at=expires_at,
            created_at=datetime.now()
        )
        await conn.execute(sql_query)

async def delete_promo_code(promo_code_id: int):
    async with engine.begin() as conn:
        sql_query = delete(PromoCode).where(PromoCode.id == promo_code_id)
        await conn.execute(sql_query)

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
        async with engine.begin() as conn:
            sql_query = insert(UserMessages).values(
                tg_id=tg_id,
                message_id=message_id,
                message_type=message_type,
                created_at=datetime.now()
            )
            await conn.execute(sql_query)

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
    async with engine.begin() as conn:
        sql_query = delete(UserMessages).where(
            UserMessages.tg_id == tg_id,
            UserMessages.message_id == message_id,
            UserMessages.message_type == message_type
        )
        await conn.execute(sql_query)

async def clear_user_messages_by_type(tg_id: int, message_types: list):
    async with engine.begin() as conn:
        sql_query = delete(UserMessages).where(
            UserMessages.tg_id == tg_id,
            UserMessages.message_type.in_(message_types)
        )
        await conn.execute(sql_query)

async def clear_user_messages(tg_id: int):
    async with engine.begin() as conn:
        sql_query = delete(UserMessages).where(UserMessages.tg_id == tg_id)
        await conn.execute(sql_query)

async def cleanup_old_messages(days: int = 7):
    cutoff_date = datetime.now() - timedelta(days=days)
    async with engine.begin() as conn:
        sql_query = delete(UserMessages).where(UserMessages.created_at < cutoff_date)
        await conn.execute(sql_query)

async def get_last_traffic_notification(tg_id: int, notification_type: str):
    async with engine.connect() as conn:
        sql_query = select(TrafficNotification).where(
            TrafficNotification.tg_id == tg_id,
            TrafficNotification.notification_type == notification_type
        ).order_by(TrafficNotification.sent_at.desc()).limit(1)
        result = (await conn.execute(sql_query)).fetchone()
        if result:
            if hasattr(result, '_mapping'):
                from db.models import TrafficNotification as TrafficNotificationModel
                notification = TrafficNotificationModel(
                    id=result._mapping.get('id'),
                    tg_id=result._mapping.get('tg_id'),
                    notification_type=result._mapping.get('notification_type'),
                    sent_at=result._mapping.get('sent_at')
                )
                return [notification]
            elif hasattr(result, '__getitem__'):
                notification = result[0]
                if hasattr(notification, 'sent_at'):
                    return [notification]
                if hasattr(notification, '_mapping'):
                    from db.models import TrafficNotification as TrafficNotificationModel
                    notification = TrafficNotificationModel(
                        id=notification._mapping.get('id'),
                        tg_id=notification._mapping.get('tg_id'),
                        notification_type=notification._mapping.get('notification_type'),
                        sent_at=notification._mapping.get('sent_at')
                    )
                    return [notification]
        return None

async def add_traffic_notification(tg_id: int, notification_type: str):
    async with engine.begin() as conn:
        sql_query = insert(TrafficNotification).values(
            tg_id=tg_id,
            notification_type=notification_type,
            sent_at=datetime.now()
        )
        await conn.execute(sql_query)

async def get_all_active_users():
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.test.isnot(None))
        result: list[VPNUsers] = (await conn.execute(sql_query)).fetchall()
        return result

async def cleanup_old_traffic_notifications(days: int = 30):
    cutoff_date = datetime.now() - timedelta(days=days)
    async with engine.begin() as conn:
        sql_query = delete(TrafficNotification).where(TrafficNotification.sent_at < cutoff_date)
        await conn.execute(sql_query)