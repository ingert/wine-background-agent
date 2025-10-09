import os
import uuid
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove
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

        # Process image
        input_image = Image.open(input_path).convert("RGBA")
        output_image = remove(input_image)

        # Optional shadow (simple drop shadow effect)
        if shadow:
            shadow_layer = ImageOps.expand(output_image, border=20, fill=(0, 0, 0, 80))
            output_image = Image.alpha_composite(shadow_layer, output_image)

        # Save processed image
        output_id = str(uuid.uuid4())
        output_filename = f"{output_id}.png"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        output_image.save(output_path)

        print(f"✅ Processed file saved at: {output_path}")

        # Return download URL
        download_url = f"/download/{output_filename}"
        return {"status": "processing", "download_url": download_url}

    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- Download endpoint ---
@app.get("/download/{file_name}")
def download_file(file_name: str):
    file_path = os.path.join(OUTPUT_DIR, file_name)
    print(f"🧾 Download requested: {file_path}")

    if not os.path.exists(file_path):
        print("⚠️ File not found!")
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    return FileResponse(file_path, media_type="image/png", filename=file_name)

# --- Root route ---
@app.get("/")
def root():
    return {"status": "running"}
