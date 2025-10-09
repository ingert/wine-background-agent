import io
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

def apply_background(image: Image.Image, bg_color: str):
    """Apply background color to an RGBA image."""
    if bg_color.lower() == "transparent":
        return image  # no change
    # Hex color support
    if bg_color.startswith("#") and len(bg_color) == 7:
        bg = Image.new("RGBA", image.size, bg_color + "FF")
    elif bg_color.lower() == "white":
        bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
    else:
        bg = Image.new("RGBA", image.size, (0, 0, 0, 0))
    return Image.alpha_composite(bg, image)

def convert_to_rgba(image: Image.Image):
    """Ensure image is RGBA (supports JPEG→PNG conversion)."""
    if image.mode != "RGBA":
        return image.convert("RGBA")
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
):
    try:
        # Read uploaded file into memory
        file_bytes = await file.read()
        input_image = Image.open(io.BytesIO(file_bytes))
        input_image = convert_to_rgba(input_image)
        input_image = resize_image(input_image)

        # Remove background
        output_image = remove(input_image, session=get_session())

        # Optional shadow
        if shadow:
            shadow_layer = ImageOps.expand(output_image, border=20, fill=(0, 0, 0, 80))
            output_image = Image.alpha_composite(shadow_layer, output_image)

        # Apply background color
        output_image = apply_background(output_image, background)

        # Save output to memory as PNG
        output_bytes = io.BytesIO()
        output_image.save(output_bytes, format="PNG")
        output_bytes.seek(0)

        return StreamingResponse(output_bytes, media_type="image/png")

    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- Root route ---
@app.get("/")
def root():
    return {"status": "running"}
