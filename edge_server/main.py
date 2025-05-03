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


# --- FRONTEND ROUTE ---
@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Product Weighing</title>
</head>
<body>
    <h1>Weigh a Product</h1>
    <p>Current weight: <span id="weight">0.0</span> g</p>
    
    <!-- Display list of products -->
    <h2>Products List</h2>
    <button onclick="fetchProducts()">Get Products</button>

    <select id="product">
        <!-- Product options will be populated here -->
    </select>

    <button onclick="sendProduct()">Send to Server</button>
    <p id="response"></p>
    <button onclick="tare()">Tare (Zero Scale)</button>

    <script>
        async function getWeight() {
            const response = await fetch('/weight');
            const data = await response.json();
            document.getElementById('weight').innerText = data.current_weight;
        }
        setInterval(getWeight, 1000);  // Update weight every second

        // Fetch list of products from the edge server and update the dropdown
        async function fetchProducts() {
            const response = await fetch('/get_products');
            const data = await response.json();
            if (data.status && data.status === "error") {
                alert("Error fetching products: " + data.details);
                return;
            }
            
            const productDropdown = document.getElementById('product');
            productDropdown.innerHTML = "";  // Clear the existing options

            // Add a default "Select" option
            const defaultOption = document.createElement("option");
            defaultOption.text = "Select a product";
            defaultOption.value = "";
            productDropdown.appendChild(defaultOption);

            // Add products as options
            data.products.forEach(product => {
                const option = document.createElement("option");
                option.value = product.name;
                option.text = `${product.name} - ${product.weight} g`;
                productDropdown.appendChild(option);
            });
        }

        // Call fetchProducts initially when the page loads
        window.onload = fetchProducts;

        // Automatically update products list every 10 minutes
        setInterval(fetchProducts, 1000 * 60 * 10);

        async function sendProduct() {
            const product = document.getElementById('product').value;
            const response = await fetch('/send_product', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product: product })
            });
            const data = await response.json();
            document.getElementById('response').innerText = data.status === "correct" 
                ? "✅ OK"
                : "❌ Not OK, wait for staff";
        }

        async function tare() {
            const response = await fetch('/tare', { method: 'POST' });
            const data = await response.json();
            if (data.status === "success") {
                alert("✅ Scale tared!");
            } else {
                alert("❌ Error during taring: " + data.details);
            }
        }
    </script>
</body>
</html>
    """


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
        )
        server_response = response.json()
        return {"status": server_response.get("status", "error")}
    except Exception as e:
        return {"status": "error", "details": str(e)}


@app.post("/tare")
async def tare_scale():
    global hx, lock
    try:
        with lock:
            if hx.zero():
                raise ValueError("Tare is unsuccessful.")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "details": str(e)}


# --- SCALE READING THREAD ---
def run_scale(
    x0: int = 10, x1: int = 393600, print_values: bool = False, calibrate: bool = False
) -> None:
    GPIO.setmode(GPIO.BCM)
    tare_btn_pin = 26
    known_weight_grams = 227
    GPIO.setup(tare_btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    global hx
    hx = HX711(dout_pin=5, pd_sck_pin=6)
    if hx.zero():
        raise ValueError("Tare is unsuccessful.")

    if calibrate:
        x0 = hx.get_data_mean()
        if not x0:
            raise ValueError("Invalid x0: ", x0)

        input("Put known weight on the scale and then press Enter: ")
        x1 = hx.get_data_mean()
        if not x1:
            raise ValueError("Invalid x1: ", x1)

    if print_values:
        print("x0: ", x0)
        print("x1: ", x1)

    try:
        global current_weight

        while True:
            with lock:
                reading = hx.get_data_mean(10)
                ratio1 = reading - x0
                ratio2 = x1 - x0
                ratio = ratio1 / ratio2

                current_weight = known_weight_grams * ratio

            time.sleep(0.2)

    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()


def register():
    print("Registering device...")
    r = requests.post(
        f"{MAIN_SERVER_URL}/register_device",
        data={"device_name": DEVICE_NAME, "shared_secret": SHARED_SECRET},
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
