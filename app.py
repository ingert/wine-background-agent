import io
import os
import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from rembg import remove, new_session

# Initialize FastAPI app
app = FastAPI(title="Wine Background Agent", description="Removes backgrounds from uploaded images.")

# Global variable for model session (lazy load)
session = None

def get_session():
    """Lazy-load the U2Net model once to save startup time."""
    global session
    if session is None:
        print("⚙️ Loading U2Net model (this may take a few seconds)...")
        session = new_session("u2net")
        print("✅ Model loaded successfully.")
    return session


# --- Health check for Render ---
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Wine background remover is running."}


# --- Background removal endpoint ---
@app.post("/auto_upload")
async def auto_upload(file: UploadFile = File(...)):
    try:
        # Read uploaded image bytes
        input_bytes = await file.read()

        # Remove background
        output_bytes = remove(input_bytes, session=get_session())

        # Generate unique filename
        image_id = str(uuid.uuid4())
        output_path = f"/tmp/{image_id}.png"

        # Save processed file
        with open(output_path, "wb") as f:
            f.write(output_bytes)

        # Return JSON with download URL
        return {
            "status": "processing_complete",
            "download_url": f"/download/{image_id}"
        }

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


# --- Download endpoint ---
@app.get("/download/{image_id}")
async def download_image(image_id: str):
    """Return the processed image from /tmp directory."""
    output_path = f"/tmp/{image_id}.png"

    if not os.path.exists(output_path):
        return JSONResponse(content={"detail": "Not Found"}, status_code=404)

    return FileResponse(output_path, media_type="image/png", filename=f"{image_id}.png")


# --- Local or Render startup ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
