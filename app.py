import os, io, uuid
from typing import Literal
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageFilter, ImageColor
import numpy as np
from rembg import remove

app = FastAPI(title="Simple Wine BG Agent", version="1.0.0")

# Root route for Render port check
@app.get("/")
def root():
    return {"status": "running"}

# Health check
@app.get("/healthz")
def health_check():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_headers=["*"], allow_methods=["*"]
)

FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=FILES_DIR), name="files")

# Background removal
def remove_bg(im: Image.Image, alpha_mode: str = "standard") -> Image.Image:
    alpha_matting = alpha_mode in ("standard", "strong")
    am_fg = 280 if alpha_mode == "strong" else 240
    am_bg = 30 if alpha_mode == "strong" else 10
    erode = 20 if alpha_mode == "strong" else 10
    return remove(
        im.convert("RGBA"),
        alpha_matting=alpha_matting,
        alpha_matting_foreground_threshold=am_fg,
        alpha_matting_background_threshold=am_bg,
        alpha_matting_erode_size=erode
    )

# Shadow generator
def auto_shadow(alpha: Image.Image, w: int, h: int, opacity: float = 0.25, blur: int = 35, size_scale: float = 1.1):
    a = np.array(alpha)
    ys, xs = np.where(a > 0)
    if len(xs) == 0:
        from PIL import Image as PImage
        return PImage.new("RGBA", (w, h), (0, 0, 0, 0))
    ymin, ymax = ys.min(), ys.max()
    xmin, xmax = xs.min(), xs.max()
    bbox_w = xmax - xmin + 1
    bbox_h = ymax - ymin + 1
    from PIL import Image, ImageDraw
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ell_w = int(bbox_w * size_scale)
    ell_h = int(max(10, bbox_h * 0.08 * size_scale))
    cx = int((xmin + xmax) / 2)
    cy = ymax
    x0 = int(cx - ell_w / 2)
    y0 = int(cy - ell_h / 2)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([x0, y0, x0 + ell_w, y0 + ell_h], fill=int(255 * opacity))
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    shadow.putalpha(mask)
    return shadow

# Upload endpoint
@app.post("/v1/auto_upload")
async def auto_upload(
    file: UploadFile = File(..., description="Billedfil (jpg/png/webp/tiff)"),
    background: str = Form("transparent", description='fx "transparent" eller "#f7f7f7"'),
    shadow: bool = Form(True),
    alpha_mode: Literal["standard", "strong"] = Form("standard")
):
    try:
        data = await file.read()
        im = Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        raise HTTPException(400, "Ugyldigt billede")

    cut = remove_bg(im, alpha_mode=alpha_mode)

    if shadow:
        W, H = cut.size
        from PIL import Image as PImage
        base = PImage.new("RGBA", (W, H), (0, 0, 0, 0))
        sh = auto_shadow(cut.getchannel("A"), W, H)
        base.alpha_composite(sh, (0, 0))
        base.alpha_composite(cut, (0, 0))
        cut = base

    bg_img = None
    if background.lower() != "transparent":
        try:
            color = ImageColor.getrgb(background)
            from PIL import Image as PImage
            bg_img = PImage.new("RGBA", cut.size, color + (255,))
        except Exception:
            raise HTTPException(400, "background skal være 'transparent' eller en gyldig farve (fx #f7f7f7)")

    from PIL import Image as PImage
    out = cut if bg_img is None else PImage.alpha_composite(bg_img, cut)

    fname = f"{uuid.uuid4().hex[:8]}.png"
    path = os.path.join(FILES_DIR, fname)
    out.save(path, "PNG")
    return {"result_url": f"/files/{fname}", "width": out.size[0], "height": out.size[1]}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
