from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from src.db.session import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String, default="ANALYST")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Vessel(Base):
    __tablename__ = "vessels"
    mmsi = Column(String, primary_key=True, index=True)
    name = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    heading = Column(Float)
    speed = Column(Float)
    last_update = Column(DateTime(timezone=True), server_default=func.now())

class Flight(Base):
    __tablename__ = "flights"
    icao24 = Column(String, primary_key=True, index=True)
    callsign = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    altitude = Column(Float)
    speed = Column(Float)
    category = Column(String)
    last_update = Column(DateTime(timezone=True), server_default=func.now())

class NewsArticle(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    url = Column(String, unique=True)
    source = Column(String)
    sentiment = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class TradeRecord(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    ticker = Column(String, index=True)
    side = Column(String) # BUY/SELL
    quantity = Column(Float)
    price = Column(Float)
    risk_snapshot = Column(JSON) # Snapshot of gates at time of trade
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
