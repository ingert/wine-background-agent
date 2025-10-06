import os, io, uuid
from typing import Literal
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageFilter, ImageColor
import numpy as np
from rembg import remove

app = FastAPI(title="Simple Wine BG Agent", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"]
)

# Files directory
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=FILES_DIR), name="files")

# Root + healthz routes
@app.get("/", include_in_schema=False)
@app.get("/healthz", include_in_schema=False)
def health_check():
    return {"status": "ok"}

# Background removal function
def remove_bg(im: Image.Image, alpha_mode: str="standard") -> Image.Image:
    alpha_matting = alp_
