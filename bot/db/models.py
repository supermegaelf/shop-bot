from sqlalchemy import Column, BigInteger, String, Boolean, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from db.base import Base

class VPNUsers(Base):
    __tablename__ = "vpnusers"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    tg_id = Column(BigInteger)
    vpn_id = Column(String(64), default="")
    test = Column(Boolean, nullable=True, default=None)
    referral_code = Column(String(16), unique=True, index=True, nullable=True)
    referred_by_id = Column(BigInteger, ForeignKey("vpnusers.tg_id"), nullable=True)
    
    referrer = relationship("VPNUsers", remote_side=[tg_id], backref="referrals", foreign_keys=[referred_by_id])

class Payments(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    tg_id = Column(BigInteger)
    lang = Column(String(64))
    payment_id = Column(String(64))
    callback = Column(String(64))
    type = Column(Integer)
    created_at = Column(DateTime)
    confirmed = Column(Boolean, default=False)
    message_id = Column(BigInteger, nullable=True)
    from_notification = Column(Boolean, default=False, nullable=True)

class PromoCode(Base):
    __tablename__ = "promo_codes"
    
    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False) 
    discount_percent = Column(Integer, nullable=False) 
    expires_at = Column(DateTime, nullable=True)  
    created_at = Column(DateTime, nullable=False)
    
class UserPromoCode(Base):
    __tablename__ = "user_promo_codes"
    
    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    tg_id = Column(BigInteger, nullable=False) 
    promo_code_id = Column(BigInteger, nullable=False)
    activated_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

class UserMessages(Base):
    __tablename__ = "user_messages"
    
    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    tg_id = Column(BigInteger, nullable=False, index=True)
    message_id = Column(BigInteger, nullable=False)
    message_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

class ReferralBonus(Base):
    __tablename__ = "referral_bonuses"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inviter_id = Column(BigInteger, nullable=False)
    referee_id = Column(BigInteger, nullable=False)
    payment_id = Column(BigInteger, nullable=True)
    bonus_days_inviter = Column(Integer, nullable=False)
    bonus_days_referee = Column(Integer, nullable=False)
    purchase_days = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

