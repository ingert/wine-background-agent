# Super Simple Wine BG Agent (Upload)

Ét endpoint, upload direkte fra ChatGPT Actions. Ingen URL-krav, ingen avancerede indstillinger.

## Kør lokalt
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080
```
Åbn `http://localhost:8080/docs`.

## Endpoint
- `POST /v1/auto_upload` (multipart)
  - `file`: billedfil
  - `background`: "transparent" (default) eller farve (fx "#f7f7f7")
  - `shadow`: bool (default true)
  - `alpha_mode`: "standard" (default) eller "strong"

Returnerer JSON med `result_url`, `width`, `height`.

## Brug i Custom GPT
Deploy offentligt, og brug `openapi.yaml` som schema-URL i Actions. Så får du en fil-uploader direkte i GPT.
