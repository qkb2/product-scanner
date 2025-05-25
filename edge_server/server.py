import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import subprocess
from threading import Thread, Lock
import RPi.GPIO as GPIO
from hx711 import HX711
import time
import requests
from dotenv import load_dotenv
import uvicorn
import statistics as st
from classifier.classifier import ImageClassifier


# Load environment variables from a .env file
load_dotenv()
GPIO.cleanup()

# --- CONFIG ---
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
]

MAIN_SERVER_URL = os.getenv(
    "MAIN_SERVER_URL", "https://your-main-server-ip:8000/verify_product"
)  # Update to use env var
SHARED_SECRET = os.getenv("SHARED_SECRET", "abc123")  # Store shared secret securely
DEVICE_NAME = os.getenv("SHARED_SECRET", "rpi1")  # Store shared secret securely
API_KEY = ""
API_KEY_FILE = "key.txt"
MAIN_SERVER_CERT = os.getenv("MAIN_SERVER_CERT", False)

# --- FASTAPI SETUP ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_weight = 0.0
lock = Lock()
hx = None

classifier = ImageClassifier()


# --- WEIGHT API ROUTE ---
@app.get("/weight")
async def get_weight():
    global current_weight
    return {"current_weight": abs(round(current_weight, 1))}


# --- TAKE PHOTO FUNCTION ---
def take_photo(filename: str = "/tmp/product.jpg") -> str:
    """Take a photo and save to filename."""
    cmd = ["libcamera-jpeg", "-o", filename, "-n", "--width", "640", "--height", "480"]
    subprocess.run(cmd, check=True)
    time.sleep(0.5)
    return filename


# --- SEND PRODUCT ROUTE ---
@app.post("/send_product")
async def send_product(request: Request):
    global current_weight
    data = await request.json()
    product_id = data.get("product_id", "unknown")

    photo_path = take_photo()
    
    pred_model_label = classifier.classify_image(photo_path)
    data = {
        "product_id": product_id,
        "weight": str(round(current_weight, 1)),
        "pred_model_label": pred_model_label
    }
    print(data)

    try:
        print("sending request")
        response = requests.post(
            f"{MAIN_SERVER_URL}/validate",
            data=data,
            headers={"Authorization": f"Bearer {API_KEY}", "api-key": API_KEY},
            verify=MAIN_SERVER_CERT,
        )
        response.raise_for_status()
        data = response.json()
        print(data)
        return {"status": data.get("result", "error")}
    except requests.exceptions.HTTPError as e:
        print(e.response.text)
        return {"status": "error", "details": str(e)}


@app.get("/get_products")
async def get_products():
    try:
        response = requests.get(
            f"{MAIN_SERVER_URL}/get_products",
            headers={"Authorization": f"Bearer {API_KEY}"},
            verify=MAIN_SERVER_CERT,
        )
        response.raise_for_status()
        data = response.json()
        return {"status": "ok", "products": data}
    except Exception as e:
        return {"status": "error", "details": str(e)}


# --- SCALE READING THREAD ---
def run_scale(
    x0: int = -837_500,
    x1: int = 84_500
) -> None:
    mw = 500

    global hx
    hx = HX711(dout_pin=5, pd_sck_pin=6)

    try:
        global current_weight

        while True:
            with lock:
                reading = hx.get_raw_data()
                avg = st.mean(reading)

                gain = mw / (x1 - x0)
                current_weight = gain * (avg - x0)

            time.sleep(0.2)
            # print(current_weight)

    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()


@app.get("/latest_photo")
async def latest_photo():
    filepath = "/tmp/product.jpg"
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="image/jpeg")
    else:
        raise HTTPException(status_code=404, detail="Image not found")


def register():
    global API_KEY

    # Try to load saved API key
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            API_KEY = f.read().strip()
        print("Loaded API key from file.")
        return

    print("Registering device...")
    r = requests.post(
        f"{MAIN_SERVER_URL}/register_device",
        data={"device_name": DEVICE_NAME, "shared_secret": SHARED_SECRET},
        verify=MAIN_SERVER_CERT,
    )
    r.raise_for_status()
    data = r.json()
    print("Registered. Device ID:", data["device_id"])
    API_KEY = data["api_key"]

    # Save API key to disk
    with open(API_KEY_FILE, "w") as f:
        f.write(API_KEY)

    return data


def unregister():
    print("Unregistering device...")
    try:
        r = requests.delete(
            f"{MAIN_SERVER_URL}/unregister_device",
            data={"device_name": DEVICE_NAME, "api_key": API_KEY},
            verify=MAIN_SERVER_CERT,
        )
        if r.status_code == 200:
            print("Unregistered successfully.")
        else:
            print("Unregistration failed:", r.text)
    except Exception as e:
        print("Unregistration error:", e)


# @app.on_event("shutdown")
# def shutdown_event():
#     unregister()


def update_model():
    try:
        version_url = f"{MAIN_SERVER_URL}/get_model_version"
        r = requests.get(version_url, verify=MAIN_SERVER_CERT)
        data = r.json()
        version = str(data.get("version", "unknown")).lower()

        current_version = classifier.get_version()

        if current_version.lower() != str(version):
            print(f"Updating model to version {version}")
            model_url = f"{MAIN_SERVER_URL}/get_model"
            r = requests.get(model_url, verify=MAIN_SERVER_CERT)
            with open("files/model.pt", "wb") as f:
                f.write(r.content)
            with open("files/model_version.txt", "w") as f:
                f.write(version)
            classifier.load_model()
    except Exception as e:
        print("Model update failed:", e)



# --- START SCALE THREAD ---
register()
update_model()
thread = Thread(target=run_scale)
thread.daemon = True
thread.start()
uvicorn.run(app=app, host="127.0.0.1", port=8000)
