import os
from threading import Thread
from dotenv import load_dotenv
from server import app, run_scale, register  # Assuming your main code is in edge_server.py

# Load environment variables
load_dotenv()

# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    import uvicorn

    try:
        # Register the device and get the API key
        register()

        # Start the scale monitoring thread
        thread = Thread(target=run_scale)
        thread.daemon = True
        thread.start()

        # Start FastAPI server (can serve over HTTPS if cert/key provided)
        uvicorn.run(
            "edge_server:app",  # adjust if your module name differs
            host="0.0.0.0",
            port=8000,
            reload=False,
            ssl_keyfile=os.getenv("SSL_KEYFILE", None),
            ssl_certfile=os.getenv("SSL_CERTFILE", None)
        )

    except Exception as e:
        print("Startup failed:", e)
