import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import subprocess
from threading import Thread, Lock
import RPi.GPIO as GPIO
from hx711 import HX711
import time
import requests
from dotenv import load_dotenv
import uvicorn

# Load environment variables from a .env file
load_dotenv()

# --- CONFIG ---
origins = [
    "http://localhost",
    "http://localhost:8000",
]

MAIN_SERVER_URL = os.getenv(
    "MAIN_SERVER_URL", "https://your-main-server-ip:8000/verify_product"
)  # Update to use env var
SHARED_SECRET = os.getenv("SHARED_SECRET", "abc123")  # Store shared secret securely
DEVICE_NAME = os.getenv("SHARED_SECRET", "rpi1")  # Store shared secret securely
API_KEY = ""
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
    product_name = data.get("product")

    photo_path = take_photo()

    files = {"image": open(photo_path, "rb")}
    payload = {
        "weight": abs(round(current_weight, 1)),
        "product": product_name,
        "rpi_id": DEVICE_NAME,
    }

    try:
        response = requests.post(
            MAIN_SERVER_URL,
            data=payload,
            files=files,
            headers={"Authorization": f"Bearer {API_KEY}"},
            verify=MAIN_SERVER_CERT  # Can be path or False
        )
        server_response = response.json()
        return {"status": server_response.get("status", "error")}
    except Exception as e:
        return {"status": "error", "details": str(e)}


# --- SCALE READING THREAD ---
def run_scale(
    x0: int = 10, x1: int = 393600, print_values: bool = False, calibrate: bool = False
) -> None:
    # GPIO.setmode(GPIO.BCM)
    # tare_btn_pin = 26
    known_weight_grams = 227
    # GPIO.setup(tare_btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    global hx
    hx = HX711(dout_pin=5, pd_sck_pin=6)
    # if hx.zero():
    #     raise ValueError("Tare is unsuccessful.")

    # if calibrate:
    #     x0 = hx.get_data_mean()
    #     if not x0:
    #         raise ValueError("Invalid x0: ", x0)

    #     input("Put known weight on the scale and then press Enter: ")
    #     x1 = hx.get_data_mean()
    #     if not x1:
    #         raise ValueError("Invalid x1: ", x1)

    # if print_values:
    #     print("x0: ", x0)
    #     print("x1: ", x1)

    try:
        global current_weight

        while True:
            with lock:
                reading = hx.get_raw_data_mean()
                ratio1 = reading - x0
                ratio2 = x1 - x0
                ratio = ratio1 / ratio2 if ratio2 != 0 else 0

                current_weight = known_weight_grams * ratio

            time.sleep(0.2)

    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()


def register():
    print("Registering device...")
    r = requests.post(
        f"{MAIN_SERVER_URL}/register_device",
        data={"device_name": DEVICE_NAME, "shared_secret": SHARED_SECRET},
        verify=MAIN_SERVER_CERT
    )
    r.raise_for_status()
    data = r.json()
    print("Registered. Device ID:", data["device_id"])
    global API_KEY
    API_KEY = data["api_key"]
    return data


# --- START SCALE THREAD ---
register()
thread = Thread(target=run_scale)
thread.daemon = True
thread.start()
uvicorn.run(app=app, host="127.0.0.1", port=8000)