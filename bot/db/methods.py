import hashlib
from enum import Enum
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, select, update, delete

from db.models import VPNUsers, Payments, PromoCode, UserPromoCode
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

async def add_payment(tg_id: int, callback: str, lang_code: str, payment_id:str, platform:PaymentPlatform, confirmed: bool = False) -> dict:
    async with engine.connect() as conn:
        sql_q = insert(Payments).values(tg_id=tg_id, payment_id=payment_id, callback=callback, lang=lang_code, type=platform.value, confirmed=confirmed, created_at=datetime.now()) 
        await conn.execute(sql_q)
        await conn.commit()

async def get_payment(payment_id, platform:PaymentPlatform) -> Payments:
    async with engine.connect() as conn:
        sql_q = select(Payments).where(Payments.payment_id == payment_id and Payments.type == platform.value)
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
        sql_query = insert(UserPromoCode).values(tg_id=tg_id, promo_code_id=promo_code_id)
        await conn.execute(sql_query)
        await conn.commit()

async def get_user_promo_discount(tg_id: int) -> float:
    async with engine.connect() as conn:
        sql_query = select(PromoCode.discount_percent).join(UserPromoCode, PromoCode.id == UserPromoCode.promo_code_id).where(UserPromoCode.tg_id == tg_id, UserPromoCode.used == False)
        result = (await conn.execute(sql_query)).fetchone()
    return result[0] if result else 0.0

async def has_confirmed_payments(tg_id: int) -> bool:
    async with engine.connect() as conn:
        sql_query = select(Payments).where(Payments.tg_id == tg_id, Payments.confirmed == True)
        result = (await conn.execute(sql_query)).fetchone()
    return result is not None

async def use_all_promo_codes(tg_id: int): # ToDo: rewrite logic to use only one promo code
    async with engine.connect() as conn:
        sql_query = update(UserPromoCode).where(UserPromoCode.tg_id == tg_id).values(used=True)
        await conn.execute(sql_query)
        await conn.commit()
    