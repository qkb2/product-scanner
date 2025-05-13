import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
from dotenv import load_dotenv
import uvicorn
import time
from threading import Thread, Lock

# --- CONFIG ---
load_dotenv()

origins = [
    "http://localhost",
    "http://localhost:8000",
]

MAIN_SERVER_URL = os.getenv("MAIN_SERVER_URL", "https://your-main-server-ip:8000/verify_product")
SHARED_SECRET = os.getenv("SHARED_SECRET", "abc123")
DEVICE_NAME = os.getenv("DEVICE_NAME", "rpi1")  # NOTE: was incorrectly assigned to SHARED_SECRET earlier
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

current_weight = 500.0  # Mocked static weight
lock = Lock()

# --- API ENDPOINTS ---

@app.get("/weight")
async def get_weight():
    return {"current_weight": round(current_weight, 1)}


@app.post("/send_product")
async def send_product(request: Request):
    global current_weight
    data = await request.json()
    product_name = data.get("product", "unknown")

    # MOCKED: Use existing static image
    photo_path = "image.jpg"
    if not os.path.exists(photo_path):
        return {"status": "error", "details": "Image not found at /tmp/product.jpg"}

    files = {"image": open(photo_path, "rb")}
    payload = {
        "weight": round(current_weight, 1),
        "product": product_name,
        "rpi_id": DEVICE_NAME,
    }

    try:
        response = requests.post(
            MAIN_SERVER_URL,
            data=payload,
            files=files,
            headers={"Authorization": f"Bearer {API_KEY}"},
            verify=MAIN_SERVER_CERT
        )
        server_response = response.json()
        return {"status": server_response.get("status", "error")}
    except Exception as e:
        return {"status": "error", "details": str(e)}


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
        verify=MAIN_SERVER_CERT
    )
    r.raise_for_status()
    data = r.json()
    print("Registered. Device ID:", data["device_id"])
    API_KEY = data["api_key"]

    # Save API key to disk
    with open(API_KEY_FILE, "w") as f:
        f.write(API_KEY)

    return data


@app.on_event("shutdown")
def shutdown_event():
    try:
        r = requests.delete(
            f"{MAIN_SERVER_URL}/unregister_device",
            data={"device_name": DEVICE_NAME, "api_key": API_KEY},
            verify=MAIN_SERVER_CERT
        )
        if r.status_code == 200:
            print("Unregistered successfully.")
        else:
            print("Unregistration failed:", r.text)
    except Exception as e:
        print("Unregistration error:", e)


# --- MOCKED SENSOR THREAD (not strictly needed for static weight, included for realism) ---
def mocked_scale_thread():
    global current_weight
    while True:
        with lock:
            current_weight = 500.0  # Always return 500g
        time.sleep(0.2)


# --- MOCKUP MAIN ---
if __name__ == "__main__":
    register()
    thread = Thread(target=mocked_scale_thread)
    thread.daemon = True
    thread.start()
    uvicorn.run(app=app, host="127.0.0.1", port=8001)
