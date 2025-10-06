import os, io, uuid
from typing import Literal
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageFilter, ImageColor
import numpy as np
from rembg import remove

# --- App setup ---
app = FastAPI(title="Simple Wine BG Agent", version="1.0.0")

# Root route for Render port check
@app.get("/")
def root():
    return {"status": "running"}

# Health check endpoint
@app.get("/healthz")
def health_check():
    return {"status": "ok"}

# CORS middleware
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

# --- Background removal ---
def remove_bg(im: Image.Image,_
