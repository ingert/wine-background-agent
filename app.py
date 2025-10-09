import io
import uuid
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove, new_session
from PIL import Image, ImageOps

# --- Initialize app ---
app = FastAPI(title="Wine Background Agent")

# --- Allow CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global model session ---
session = None

def get_session():
    global session
    if session is None:
        print("⚙️ Loading U2NetP model (smaller & faster)...")
        session = new_session("u2netp")
        print("✅ Model loaded successfully.")
    return session

def resize_image(image: Image.Image, max_size=1024):
    """Resize image to max dimension to prevent timeouts."""
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size))
    return image

# --- Health check route ---
@app.get("/healthz")
def health_check():
    return {"status":
