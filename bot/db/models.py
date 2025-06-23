from sqlalchemy import Column, BigInteger, String, Boolean, Integer, DateTime
from datetime import datetime

from db.base import Base

class VPNUsers(Base):
    __tablename__ = "vpnusers"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    tg_id = Column(BigInteger)
    vpn_id = Column(String(64), default="")
    test = Column(Boolean, nullable=True, default=None) # null - trial available, true - test subscription, false - trial expired

class Payments(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    tg_id = Column(BigInteger)
    lang = Column(String(64))
    payment_id = Column(String(64))
    callback = Column(String(64))
    type=Column(Integer)
    created_at=Column(DateTime)
    confirmed=Column(Boolean, default=False)

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