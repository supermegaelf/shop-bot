from sqlalchemy import Column, BigInteger, String, Boolean, Integer, DateTime

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
