from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from main_server.db import SessionLocal
from models import Device

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_device(api_key: str = Header(...), db: Session = Depends(get_db)) -> Device:
    device = db.query(Device).filter_by(api_key=api_key).first()
    if not device:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return device

api_key_header = Header(...)
