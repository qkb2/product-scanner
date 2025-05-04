from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from main_server.db import Base

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    incidents = relationship("Incident", back_populates="device")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    weight = Column(Float(), nullable=False)
    incidents = relationship("Incident", back_populates="product")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))
    weight = Column(Float())
    image_path = Column(String)
    result = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="incidents")
    device = relationship("Device", back_populates="incidents")
