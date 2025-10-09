import os
import uuid
import io
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove, new_session
from PIL import Image, ImageOps
from pathlib import Path

# =========================================================
# ⚙️ Setup
# =========================================================
app = FastAPI(title="Wine Background Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

session = None  # Lazy model loading


# =========================================================
# 🧠 Helper functions
# =========================================================
def get_session():
    """Load the rembg model once per process."""
    global session
    if session is None:
        print("⚙️ Loading U2NetP model (this may take a few seconds)...")
        session = new_session("u2netp")
        print("✅ Model loaded successfully.")
    return session


def process_image(image_data: bytes, background: str = "transparent") -> Image.Image:
    """Removes background and applies the given background color or transparency."""
    input_image = Image.open(io.BytesIO(image_data)).convert("RGBA")
    session = get_session()

    # Remove background
    output_image = remove(input_image, session=session).convert("RGBA")

    # Handle background choice
    if background.lower() != "transparent":
        bg_color = background if background.startswith("#") else "white"
        bg = Image.new("RGBA", output_image.size, bg_color)
        bg.alpha_composite(output_image)
        output_image = bg

    return output_image


# =========================================================
# 🚀 Routes
# =========================================================
@app.get("/")
async def root():
    return {"message": "✅ Wine Background Agent is running!"}


@app.post("/v1/auto_upload")
async def auto_upload(
    request: Request,
    file: UploadFile = File(...),
    background: str = Form("transparent")
):
    """Handles upload, background removal, and saving."""
    try:
        # Save upload
        upload_id = str(uuid.uuid4())
        upload_path = UPLOAD_DIR / f"{upload_id}_{file.filename}"
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
        print(f"📸 Uploaded file saved at: {upload_path}")

        # Process
        output_image = process_image(content, background=background)

        # Save processed file
        output_filename = f"{upload_id}.png"
        output_path = PROCESSED_DIR / output_filename
        output_image.save(output_path, format="PNG")
        print(f"✅ Processed file saved at: {output_path}")

        # Return public URL
        download_url = f"{request.base_url}download/{output_filename}"
        return {"status": "success", "download_url": download_url}

    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Serve processed images."""
    file_path = PROCESSED_DIR / filename
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    return FileResponse(
        file_path,
        media_type="image/png",
        filename=filename
    )


# =========================================================
# 🧪 Run locally
# =========================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
