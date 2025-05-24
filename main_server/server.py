# main_server/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from uuid import uuid4
import os
from dotenv import load_dotenv
import uvicorn

from main_server.db import SessionLocal, engine, Base
from main_server.models import Product, Incident, Device
from main_server.auth import get_current_device
from classifier.classifier import classify_image, get_version

load_dotenv()

SHARED_SECRET = os.getenv("SHARED_SECRET", "abc123")  # Store shared secret securely

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:3000",  # React default dev port
    "http://127.0.0.1:3000",
    "https://localhost:3000",
    "https://127.0.0.1:3000",
    "http://localhost:5173",  # Vite (optional)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register_device")
def register_device(
    device_name: str = Form(...),
    shared_secret: str = Form(...),
    db: Session = Depends(get_db),
):
    if shared_secret != SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid shared secret")

    # Check if the device already exists
    device = db.query(Device).filter_by(name=device_name).first()

    if device:
        # Update existing device with new API key
        device.api_key = str(uuid4())
        db.commit()
        db.refresh(device)
        return {
            "message": "Device re-registered",
            "device_id": device.id,
            "api_key": device.api_key,
        }
    else:
        # Create new device
        device = Device(name=device_name, api_key=str(uuid4()))
        db.add(device)
        db.commit()
        db.refresh(device)
        return {
            "message": "Device registered",
            "device_id": device.id,
            "api_key": device.api_key,
        }


@app.delete("/unregister_device")
def unregister_device(
    device_name: str = Form(...),
    api_key: str = Form(...),
    db: Session = Depends(get_db),
):
    device = (
        db.query(Device)
        .filter(Device.name == device_name, Device.api_key == str(api_key))
        .first()
    )

    if not device:
        raise HTTPException(
            status_code=404, detail="Device not found or invalid credentials"
        )

    db.delete(device)
    db.commit()
    return {"detail": "Device unregistered successfully"}


@app.get("/get_devices")
def get_devices(db: Session = Depends(get_db), shared_secret: str = None):
    if shared_secret != SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid shared secret")

    devices = db.query(Device).all()
    return [{"id": d.id, "name": d.name} for d in devices]


@app.post("/remove_device")
def remove_device(
    device_id: int = Form(...),
    shared_secret: str = Form(...),
    db: Session = Depends(get_db),
):
    if shared_secret != SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid shared secret")

    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    return {"message": f"Device '{device.name}' removed."}


@app.post("/validate")
def validate(
    product_id: int = Form(...),
    pred_model_label: int = Form(),
    weight: float = Form(...),
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):
    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # # Save image
    # if image.filename is not None:
    #     img_path = os.path.join(UPLOAD_DIR, image.filename)
    # else:
    #     HTTPException(status_code=400, detail="Image missing")
    # with open(img_path, "wb") as buffer:
    #     shutil.copyfileobj(image.file, buffer)

    # # Classify
    # pred_model_label = classify_image(img_path)
    pred_product = db.query(Product).filter_by(model_label=pred_model_label).first()

    if pred_product is not None:
        print(f"Predicted id: {pred_model_label} with label {pred_product.name}")
    else:
        print(f"Predicted id: {pred_model_label} without label")

    is_valid = (pred_model_label == product.model_label) and (
        product.weight - 15 <= weight <= product.weight + 15
    )
    if not isinstance(is_valid, bool):
        raise HTTPException(status_code=200, detail="Internal error")
    is_valid = bool(is_valid)

    print(f"Is valid: {is_valid}")

    incident = Incident(
        product_id=product.id,
        predicted_label=pred_model_label,
        device_id=device.id,
        weight=weight,
        result="correct" if is_valid else "incorrect",
    )
    db.add(incident)
    db.commit()

    return {"result": incident.result}


@app.get("/incidents/last")
def last_incidents(count: int = 10, db: Session = Depends(get_db)):
    incidents = (
        db.query(Incident).order_by(Incident.timestamp.desc()).limit(count).all()
    )
    return [
        {
            "product": i.product.name,
            "label": i.product.model_label,
            "predicted label": i.predicted_label,
            "weight": i.weight,
            "result": i.result,
            "timestamp": i.timestamp,
            "device": i.device.name if i.device else None,
        }
        for i in incidents
    ]


@app.post("/add_product")
def add_product(
    name: str = Form(...),
    weight: float = Form(...),
    model_id: int = Form(...),
    db: Session = Depends(get_db),
    shared_secret: str = Form(...),
):
    if (
        shared_secret != SHARED_SECRET
    ):  # You can replace this with an env var or secret manager
        raise HTTPException(status_code=403, detail="Invalid shared secret")

    existing = db.query(Product).filter_by(name=name).first()
    if existing:
        existing.weight = weight
        existing.model_label = model_id
        db.commit()
        return {"message": "Updated"}
    p = Product(name=name, weight=weight, model_id=model_id)
    db.add(p)
    db.commit()
    return {"message": "Added"}


@app.get("/get_products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [{"id": p.id, "name": p.name, "weight": p.weight} for p in products]


@app.post("/reset_devices")
def reset_devices(db: Session = Depends(get_db), shared_secret: str = Form(...)):
    if shared_secret != SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid shared secret")

    deleted = db.query(Device).delete()
    db.commit()
    return {"message": f"Reset successful. {deleted} devices removed."}


@app.get("/get_model_version")
def get_model_version():
    return {"version": get_version()}


@app.get("/get_model")
def get_model():
    return FileResponse("files/model.pt")


uvicorn.run(
    app=app,
    host="0.0.0.0",
    port=8000,
    ssl_certfile=os.getenv("SSL_CERTFILE"),
    ssl_keyfile=os.getenv("SSL_KEYFILE"),
)
