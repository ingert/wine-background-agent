from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
from rembg import remove
import uuid

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

PROCESSED_DIR = Path("processed")
PROCESSED_DIR.mkdir(exist_ok=True)


def process_image(input_path: Path, output_path: Path):
    """Remove background and save to output_path."""
    with input_path.open("rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    with output_path.open("wb") as f:
        f.write(output_bytes)


@app.post("/v1/auto_upload")
async def auto_upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Save uploaded file
    file_ext = Path(file.filename).suffix
    temp_filename = UPLOAD_DIR / f"{uuid.uuid4()}{file_ext}"
    with temp_filename.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Set output path
    output_filename = PROCESSED_DIR / f"{uuid.uuid4()}.png"

    # Add background processing
    background_tasks.add_task(process_image, temp_filename, output_filename)

    # Return download URL (user will need to poll or visit later)
    return {"status": "processing", "download_url": f"/download/{output_filename.name}"}


@app.get("/download/{filename}")
async def download(filename: str):
    file_path = PROCESSED_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    return {"error": "File not ready yet"}
