import io
import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from rembg import remove, new_session

# Initialize FastAPI app
app = FastAPI(title="Wine Background Agent", description="Removes backgrounds from uploaded images.")

# Global variable for model session (lazy load)
session = None

def get_session():
    global session
    if session is None:
        print("⚙️ Loading U2Net model (this may take a few seconds)...")
        session = new_session("u2net")
        print("✅ Model loaded successfully.")
    return session


# Health check for Render (important!)
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Wine background remover is running."}


# Main endpoint for background removal
@app.post("/auto_upload")
async def auto_upload(file: UploadFile = File(...)):
    try:
        # Read uploaded image bytes
        input_bytes = await file.read()

        # Remove background using rembg
        output_bytes = remove(input_bytes, session=get_session())

        # Return processed image as PNG
        return StreamingResponse(io.BytesIO(output_bytes), media_type="image/png")

    except Exception as e:
        # Handle any errors gracefully
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


# --- Local or Render startup ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))  # Render dynamically sets PORT
    print(f"🚀 Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
