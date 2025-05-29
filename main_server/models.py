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
    address = Column(String, default="http://127.0.0.1:8000")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    weight = Column(Float(), nullable=False)
    model_label = Column(Integer)
    incidents = relationship("Incident", back_populates="product")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    predicted_label = Column(Integer)
    device_id = Column(Integer, ForeignKey("devices.id"))
    weight = Column(Float())
    result = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="incidents")
    device = relationship("Device", back_populates="incidents")
