import os
from dotenv import load_dotenv
from server import app

# Load environment variables
load_dotenv()

# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    import uvicorn

    try:
        # Start FastAPI server (can serve over HTTPS if cert/key provided)
        uvicorn.run(
            "main_server:app",  # adjust if your module name differs
            host="0.0.0.0",
            port=8000,
            reload=False,
            ssl_keyfile=os.getenv("SSL_KEYFILE", None),
            ssl_certfile=os.getenv("SSL_CERTFILE", None)
        )

    except Exception as e:
        print("Startup failed:", e)
