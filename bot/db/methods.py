import hashlib
from enum import Enum

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, select, update, delete

from db.models import VPNUsers, Payments
import glv

class PaymentPlatform(Enum):
    yookassa = 0
    cryptomus = 1
    telegram = 2

engine = create_async_engine(glv.config['DB_URL'])

async def create_vpn_profile(tg_id: int):
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.tg_id == tg_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
        if result is not None:
            return
        hash = hashlib.md5(str(tg_id).encode()).hexdigest()
        sql_query = insert(VPNUsers).values(tg_id=tg_id, vpn_id=hash)
        await conn.execute(sql_query)
        await conn.commit()

async def get_marzban_profile_db(tg_id: int) -> VPNUsers:
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
    return result.test

async def disable_trial_availability(tg_id):
    async with engine.connect() as conn:
        sql_q = update(VPNUsers).where(VPNUsers.tg_id == tg_id).values(test=False)
        await conn.execute(sql_q)
        await conn.commit()

async def add_payment(tg_id: int, callback: str, lang_code: str, payment_id:str, platform:PaymentPlatform) -> dict:
    async with engine.connect() as conn:
        sql_q = insert(Payments).values(tg_id=tg_id, payment_id=payment_id, callback=callback, lang=lang_code, platform=platform.value)
        await conn.execute(sql_q)
        await conn.commit()

async def get_payment(payment_id, platform:PaymentPlatform) -> Payments:
    async with engine.connect() as conn:
        sql_q = select(Payments).where(Payments.payment_id == payment_id and Payments.platform == platform.value)
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
    