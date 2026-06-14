from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    created_orders = relationship("WorkOrder", back_populates="creator", foreign_keys="WorkOrder.creator_id")
    assigned_orders = relationship("WorkOrder", back_populates="assignee", foreign_keys="WorkOrder.assignee_id")
    repair_records = relationship("RepairRecord", back_populates="repairer")


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    address = Column(String(200), nullable=False)
    contact = Column(String(50))
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    chargers = relationship("Charger", back_populates="station", cascade="all, delete-orphan")


class Charger(Base):
    __tablename__ = "chargers"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    serial_number = Column(String(50), unique=True, nullable=False)
    model = Column(String(50))
    total_guns = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)

    station = relationship("Station", back_populates="chargers")
    guns = relationship("ChargingGun", back_populates="charger", cascade="all, delete-orphan")


class ChargingGun(Base):
    __tablename__ = "charging_guns"

    id = Column(Integer, primary_key=True, index=True)
    charger_id = Column(Integer, ForeignKey("chargers.id"), nullable=False)
    gun_number = Column(String(20), nullable=False)
    status = Column(String(20), default="online")
    last_check_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    charger = relationship("Charger", back_populates="guns")
    work_orders = relationship("WorkOrder", back_populates="gun")


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False)
    order_type = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(String(20), default="normal")
    status = Column(String(20), default="pending")
    gun_id = Column(Integer, ForeignKey("charging_guns.id"))
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    take_gun_offline = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    gun = relationship("ChargingGun", back_populates="work_orders")
    creator = relationship("User", back_populates="created_orders", foreign_keys=[creator_id])
    assignee = relationship("User", back_populates="assigned_orders", foreign_keys=[assignee_id])
    repair_records = relationship("RepairRecord", back_populates="work_order", cascade="all, delete-orphan")


class RepairRecord(Base):
    __tablename__ = "repair_records"

    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    repairer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    arrive_time = Column(DateTime, default=datetime.utcnow)
    voltage_measurement = Column(Float)
    parts_replaced = Column(Boolean, default=False)
    parts_description = Column(Text)
    repair_description = Column(Text)
    photo_urls = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    work_order = relationship("WorkOrder", back_populates="repair_records")
    repairer = relationship("User", back_populates="repair_records")
