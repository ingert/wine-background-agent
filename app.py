import os
import uuid
from fastapi import FastAPI, File, UploadFile, Form, Request
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

# --- Local storage setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Health check ---
@app.get("/healthz")
def health_check():
    return {"status": "ok"}

# --- Main upload/processing route ---
@app.post("/v1/auto_upload")
async def auto_upload(
    request: Request,
    file: UploadFile = File(...),
    background: str = Form("transparent"),  # 'transparent' or e.g. "#ffffff"
    shadow: bool = Form(False),
):
    try:
        # Save uploaded file
        input_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{input_id}_{file.filename}")
        with open(input_path, "wb") as f:
            f.write(await file.read())
        print(f"📸 Uploaded file saved at: {input_path}")

        # Remove background
        input_image = Image.open(input_path).convert("RGBA")
        output_image = remove(input_image)
        output_image = output_image.convert("RGBA")

        # Apply shadow if requested
        if shadow:
            shadow_layer = Image.new("RGBA", output_image.size, (0, 0, 0, 0))
            shadow_border = 20
            expanded = ImageOps.expand(output_image, border=shadow_border, fill=(0, 0, 0, 80))
            shadow_layer.paste(expanded, (0, 0), expanded)
            output_image = Image.alpha_composite(shadow_layer, output_image)

        # Apply background color if not transparent
        if background.lower() != "transparent":
            bg_image = Image.new("RGBA", output_image.size, background)
            output_image = Image.alpha_composite(bg_image, output_image)

        # Save processed image
        output_id = str(uuid.uuid4())
        output_filename = f"{output_id}.png"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        output_image.save(output_path)
        print(f"✅ Processed file saved at: {output_path}")

        # Return absolute download URL
        base_url = str(request.base_url).rstrip("/")
        download_url = f"{base_url}/download/{output_filename}"

        return {"status": "success", "download_url": download_url}

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

# --- Run locally ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

