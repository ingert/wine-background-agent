import os, io, uuid
from typing import Literal
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageFilter, ImageColor
import numpy as np
from rembg import remove

app = FastAPI(title="Simple Wine BG Agent", version="1.0.0")

# Root + Health check
@app.get("/")
@app.get("/healthz")
def health_check():
    return {"status": "ok"}

# Enable CORS
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_headers=["*"], allow_methods=["*"]
)

# File storage
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=FILES_DIR), name="files")

# Background removal
def remove_bg(im: Image.Image, alpha_mode: str="standard") -> Image.Image:
    alpha_matting = alpha_mode in ("standard", "strong")
    am_fg = 280 if alpha_mode == "strong" else 240
    am_bg = 30 if alpha_mode == "strong" else 10
    erode = 20 if alpha_mode ==_
