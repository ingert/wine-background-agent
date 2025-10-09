import os
import uuid
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
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

# --- Directories ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Global model session ---
session = None

def get_session():
    global session
    if session is None:
        print("⚙️ Loading U2NetP model at startup (may take a few seconds)...")
        session = new_session("u2netp")
        print("✅ Model loaded successfully.")
    return session

# --- Preload model on startup ---
@app.on_event("startup")
def startup_event():
    get_session()


# --- Utility: resize image to max dimension ---
def resize_image(image: Image.Image, max_size: int = 1024) -> Image.Image:
    w, h = image.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        new_size = (int(w * scale), int(h * scale))
        return image.resize(new_size, Image.ANTIALIAS)
    return image


# --- Health check route ---
@app.get("/healthz")
def health_check():
    return {"status": "ok"}


# --- Main upload/processing route ---
@app.post("/v1/auto_upload")
async def auto_upload(
    file: UploadFile = File(...),
    background: str = Form("transparent"),
    shadow: bool = Form(False),
    alpha_mode: str = Form("standard"),
):
    try:
        # Save uploaded file
        input_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{input_id}_{file.filename}")

        with open(input_path, "wb") as f:
            f.write(await file.read())

        print(f"📸 Uploaded file saved at: {input_path}")

        # Open and resize image
        input_image = Image.open(input_path).convert("RGBA")
        input_image = resize_image(input_image, max_size=1024)

        # Remove background
        output_image = remove(input_image, session=get_session())

        # Optional shadow (simple drop shadow)
        if shadow:
            shadow_layer = ImageOps.expand(output_image, border=20, fill=(0, 0, 0, 80))
            output_image = Image.alpha_composite(shadow_layer, output_image)

        # Save processed image
        output_id = str(uuid.uuid4())
        output_filename = f"{output_id}.png"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        output_image.save(output_path)

        print(f"✅ Processed
