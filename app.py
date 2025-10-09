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
        file_bytes = await file.read()
        with open(input_path, "wb") as f:
            f.write(file_bytes)
        print(f"📸 Uploaded file saved at: {input_path}")

        # Remove background correctly
        session = get_session()
        from io import BytesIO

        output_bytes = remove(file_bytes, session=session)
        output_image = Image.open(BytesIO(output_bytes)).convert("RGBA")  # proper RGBA

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
