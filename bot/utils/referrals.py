import secrets
import string
import math
import logging
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import VPNUsers, ReferralBonus, Payments
from db.methods import engine, get_vpn_user
from utils.ephemeral import EphemeralNotification
from utils.lang import get_i18n_string
from keyboards.referral import get_referral_notification_keyboard
import glv

REFERRAL_CODE_LENGTH = 9
REFERRAL_CODE_ALPHABET = string.ascii_uppercase + string.digits

def generate_referral_code() -> str:
    return ''.join(secrets.choice(REFERRAL_CODE_ALPHABET) for _ in range(REFERRAL_CODE_LENGTH))

async def ensure_referral_code(tg_id: int) -> Optional[str]:
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.tg_id == tg_id)
        result = (await conn.execute(sql_query)).fetchone()
        
        if not result:
            return None
        
        if result.referral_code:
            return result.referral_code
    
    for attempt in range(25):
        code = generate_referral_code()
        
        async with engine.connect() as conn:
            check_query = select(VPNUsers).where(VPNUsers.referral_code == code)
            existing = (await conn.execute(check_query)).fetchone()
            
            if not existing:
                async with engine.begin() as conn:
                    from sqlalchemy import update
                    update_query = update(VPNUsers).where(VPNUsers.tg_id == tg_id).values(referral_code=code)
                    await conn.execute(update_query)
                return code
    
    logging.error(f"Failed to generate unique referral code for user {tg_id} after 25 attempts")
    return None

async def get_user_by_referral_code(code: str) -> Optional[VPNUsers]:
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.referral_code == code.upper())
        result = (await conn.execute(sql_query)).fetchone()
    return result

async def set_referrer(tg_id: int, referrer_id: int) -> bool:
    if tg_id == referrer_id:
        return False
    
    async with engine.begin() as conn:
        from sqlalchemy import update
        update_query = update(VPNUsers).where(VPNUsers.tg_id == tg_id).values(referred_by_id=referrer_id)
        await conn.execute(update_query)
    
    return True

async def get_referral_stats(tg_id: int) -> Dict:
    async with engine.connect() as conn:
        invited_query = select(func.count()).select_from(VPNUsers).where(VPNUsers.referred_by_id == tg_id)
        invited_count = (await conn.execute(invited_query)).scalar() or 0
        
        earned_query = select(func.sum(ReferralBonus.bonus_days_inviter)).where(ReferralBonus.inviter_id == tg_id)
        earned_days = (await conn.execute(earned_query)).scalar() or 0
    
    return {
        'invited_count': invited_count,
        'earned_days': earned_days
    }

async def apply_referral_bonuses(referee_id: int, purchase_days: int, payment_id: int = None, lang: str = 'ru') -> Dict:
    inviter_percent = glv.config.get('REFERRAL_BONUS_PERCENT_INVITER', 10)
    referee_percent = glv.config.get('REFERRAL_BONUS_PERCENT_REFEREE', 5)
    
    user = await get_vpn_user(referee_id)
    if not user or not user.referred_by_id:
        return {'success': False, 'reason': 'no_referrer'}
    
    inviter_id = user.referred_by_id
    
    bonus_days_inviter = max(1, math.ceil(purchase_days * inviter_percent / 100))
    bonus_days_referee = max(1, math.ceil(purchase_days * referee_percent / 100))
    
    async with engine.begin() as conn:
        from sqlalchemy import insert
        insert_query = insert(ReferralBonus).values(
            inviter_id=inviter_id,
            referee_id=referee_id,
            payment_id=payment_id,
            bonus_days_inviter=bonus_days_inviter,
            bonus_days_referee=bonus_days_referee,
            purchase_days=purchase_days,
            created_at=datetime.now()
        )
        await conn.execute(insert_query)
    
    try:
        from panel import get_panel
        panel = get_panel()
        
        inviter_user = await get_vpn_user(inviter_id)
        if inviter_user and inviter_user.vpn_id:
            try:
                inviter_profile = await panel.get_panel_user(inviter_id)
                if inviter_profile and inviter_profile.expire:
                    from datetime import timedelta
                    new_expire = inviter_profile.expire + timedelta(days=bonus_days_inviter)
                    
                    user_data = await panel._get_user_by_username(inviter_user.vpn_id)
                    if user_data:
                        update_payload = {
                            'uuid': user_data['uuid'],
                            'expireAt': new_expire.isoformat().replace('+00:00', 'Z')
                        }
                        await panel.client.patch(f"/users", json=update_payload)
                        
                        stats = await get_referral_stats(inviter_id)
                        inviter_lang = 'ru'
                        
                        text = get_i18n_string("referral_notification_inviter", inviter_lang).format(
                            days=bonus_days_inviter,
                            total_days=stats['earned_days']
                        )
                        
                        keyboard = get_referral_notification_keyboard(inviter_lang)
                        
                        await EphemeralNotification.send_ephemeral(
                            bot=glv.bot,
                            chat_id=inviter_id,
                            text=text,
                            reply_markup=keyboard,
                            lang=inviter_lang
                        )
            except Exception as e:
                logging.error(f"Failed to apply bonus to inviter {inviter_id}: {e}")
        
        referee_user = await get_vpn_user(referee_id)
        if referee_user and referee_user.vpn_id:
            try:
                referee_profile = await panel.get_panel_user(referee_id)
                if referee_profile and referee_profile.expire:
                    from datetime import timedelta
                    new_expire = referee_profile.expire + timedelta(days=bonus_days_referee)
                    
                    user_data = await panel._get_user_by_username(referee_user.vpn_id)
                    if user_data:
                        update_payload = {
                            'uuid': user_data['uuid'],
                            'expireAt': new_expire.isoformat().replace('+00:00', 'Z')
                        }
                        await panel.client.patch(f"/users", json=update_payload)
            except Exception as e:
                logging.error(f"Failed to apply bonus to referee {referee_id}: {e}")
        
    except Exception as e:
        logging.error(f"Failed to apply referral bonuses: {e}")
        return {'success': False, 'reason': 'bonus_application_failed'}
    
    return {
        'success': True,
        'bonus_days_inviter': bonus_days_inviter,
        'bonus_days_referee': bonus_days_referee
    }

async def get_admin_referral_stats() -> Dict:
    async with engine.connect() as conn:
        total_referrers_query = select(func.count(func.distinct(VPNUsers.tg_id))).select_from(VPNUsers).where(VPNUsers.referred_by_id.isnot(None))
        total_referrals = (await conn.execute(total_referrers_query)).scalar() or 0
        
        active_referrers_query = select(func.count(func.distinct(VPNUsers.referred_by_id))).select_from(VPNUsers).where(VPNUsers.referred_by_id.isnot(None))
        active_referrers = (await conn.execute(active_referrers_query)).scalar() or 0
        
        total_bonus_query = select(func.sum(ReferralBonus.bonus_days_inviter + ReferralBonus.bonus_days_referee)).select_from(ReferralBonus)
        total_bonus = (await conn.execute(total_bonus_query)).scalar() or 0
        
        purchased_query = select(func.count(func.distinct(Payments.tg_id))).select_from(Payments).join(VPNUsers, Payments.tg_id == VPNUsers.tg_id).where(VPNUsers.referred_by_id.isnot(None), Payments.confirmed == True)
        purchased_count = (await conn.execute(purchased_query)).scalar() or 0
        
        conversion = round((purchased_count / total_referrals * 100), 1) if total_referrals > 0 else 0
        avg_bonus = round((total_bonus / active_referrers), 1) if active_referrers > 0 else 0
        
        top_referrer_query = select(VPNUsers.tg_id, func.count(VPNUsers.tg_id).label('count')).select_from(VPNUsers).where(VPNUsers.referred_by_id.isnot(None)).group_by(VPNUsers.referred_by_id).order_by(func.count(VPNUsers.tg_id).desc()).limit(1)
        top_result = (await conn.execute(top_referrer_query)).first()
        
        top_referrer_id = None
        top_referrer_count = 0
        top_referrer_days = 0
        
        if top_result:
            top_referrer_id = top_result[0]
            top_referrer_count = top_result[1]
            
            top_bonus_query = select(func.sum(ReferralBonus.bonus_days_inviter)).where(ReferralBonus.inviter_id == top_referrer_id)
            top_referrer_days = (await conn.execute(top_bonus_query)).scalar() or 0
    
    return {
        'referrers_count': active_referrers,
        'referrals_count': total_referrals,
        'active_referrers': active_referrers,
        'conversion': conversion,
        'purchased': purchased_count,
        'total': total_referrals,
        'total_bonus': total_bonus,
        'avg_bonus': avg_bonus,
        'top_referrer_id': top_referrer_id,
        'top_referrer_count': top_referrer_count,
        'top_referrer_days': top_referrer_days
    }

async def get_referrers_list(page: int = 1, per_page: int = 5) -> Dict:
    offset = (page - 1) * per_page
    
    async with engine.connect() as conn:
        referrers_query = select(
            VPNUsers.tg_id,
            VPNUsers.referred_by_id,
            func.count(VPNUsers.tg_id).label('referrals_count')
        ).select_from(VPNUsers).where(
            VPNUsers.referred_by_id.isnot(None)
        ).group_by(
            VPNUsers.referred_by_id
        ).order_by(
            func.count(VPNUsers.tg_id).desc()
        ).limit(per_page).offset(offset)
        
        results = (await conn.execute(referrers_query)).fetchall()
        
        total_query = select(func.count(func.distinct(VPNUsers.referred_by_id))).select_from(VPNUsers).where(VPNUsers.referred_by_id.isnot(None))
        total = (await conn.execute(total_query)).scalar() or 0
    
    referrers = []
    for row in results:
        referrer_id = row.referred_by_id
        count = row.referrals_count
        
        async with engine.connect() as conn:
            bonus_query = select(func.sum(ReferralBonus.bonus_days_inviter)).where(ReferralBonus.inviter_id == referrer_id)
            days = (await conn.execute(bonus_query)).scalar() or 0
        
        referrers.append({
            'referrer_id': referrer_id,
            'referrals_count': count,
            'earned_days': days
        })
    
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    return {
        'referrers': referrers,
        'page': page,
        'total_pages': total_pages,
        'total': total
    }

async def get_user_referrals(user_id: int, page: int = 1, per_page: int = 5) -> Dict:
    offset = (page - 1) * per_page
    
    async with engine.connect() as conn:
        referrals_query = select(VPNUsers).where(VPNUsers.referred_by_id == user_id).limit(per_page).offset(offset)
        results = (await conn.execute(referrals_query)).fetchall()
        
        total_query = select(func.count()).select_from(VPNUsers).where(VPNUsers.referred_by_id == user_id)
        total = (await conn.execute(total_query)).scalar() or 0
    
    referrals = []
    for row in results:
        referee_id = row.tg_id
        
        async with engine.connect() as conn:
            purchases_query = select(func.count()).select_from(Payments).where(Payments.tg_id == referee_id, Payments.confirmed == True)
            purchases = (await conn.execute(purchases_query)).scalar() or 0
            
            bonus_query = select(func.sum(ReferralBonus.bonus_days_inviter)).where(ReferralBonus.inviter_id == user_id, ReferralBonus.referee_id == referee_id)
            days = (await conn.execute(bonus_query)).scalar() or 0
        
        referrals.append({
            'referee_id': referee_id,
            'purchases': purchases,
            'earned_days': days
        })
    
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    return {
        'referrals': referrals,
        'page': page,
        'total_pages': total_pages,
        'total': total
    }
