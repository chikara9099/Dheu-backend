# Dheu Backend (dheu-backend)

This small backend exposes two FastAPI sub-apps under `/roughness` and `/news`.

This README shows how to build and run the Docker image locally and how to deploy to Railway using the provided `Dockerfile`.

## What is in the folder

- `main.py` - FastAPI app that mounts the two sub-apps.
- `apis/` - `ocean_news.py` and `sea_roughness.py` (external API integrations; require credentials).
- `requirements.txt` - Python dependencies.
- `Dockerfile` - Production-oriented Dockerfile (uses Python 3.11-slim, installs GDAL for rasterio).

## Environment variables

This app expects the following environment variables (set them in Railway or locally in a `.env` file):

- `GEMINI_API_KEY` - required by `apis/ocean_news.py` (Gemini/Google GenAI client key).
- `CDSE_CLIENT_ID` - required by `apis/sea_roughness.py` (Sentinel Hub client id).
- `CDSE_CLIENT_SECRET` - required by `apis/sea_roughness.py` (Sentinel Hub client secret).

Note: `apis/ocean_news.py` will raise an exception at import time if `GEMINI_API_KEY` is missing.

## Build and run locally (PowerShell)

From the `dheu-backend` directory:

```powershell
# Build image (tags: dheu-backend:local)
docker build -t dheu-backend:local .

# Run container (map port 8000 -> 8000 and pass required env vars)
# Replace values with your real secrets or .env loader
docker run --rm -p 8000:8000 `
  -e GEMINI_API_KEY="your_gemini_key" `
  -e CDSE_CLIENT_ID="your_cdse_client_id" `
  -e CDSE_CLIENT_SECRET="your_cdse_client_secret" `
  dheu-backend:local

# Then visit http://localhost:8000/ or http://localhost:8000/roughness or /news
```

If you use a `.env` file locally, consider using `docker run --env-file .env ...`.

## Quick test

```powershell
# After container is running, test root
curl http://localhost:8000/
```

## Deploy to Railway (Dockerfile method)

Railway supports building from a `Dockerfile` directly. Steps:

1. Create a new Railway project and link it to this repository, or use the Railway dashboard to create a new service and select "Deploy from GitHub".
2. Ensure Railway sees the `Dockerfile` at the repo root or set the service's build path to the `dheu-backend` folder.
3. In Railway's service Settings → Variables, set the environment variables listed above (`GEMINI_API_KEY`, `CDSE_CLIENT_ID`, `CDSE_CLIENT_SECRET`).
4. Railway will build the image using the `Dockerfile`. The app listens on the port Railway provides via the `PORT` env var (the Dockerfile uses `${PORT}`), so no extra configuration is needed.

Alternatively, use the Railway CLI:

```powershell
# Install railway CLI (if not already)
# https://docs.railway.app/develop/cli

# From project root:
railway init  # follow prompts
railway link   # link to an existing project
railway up     # this will build and deploy the Dockerfile in the current folder
```

## Troubleshooting

- rasterio / GDAL errors: ensure the `Dockerfile` includes system packages `gdal-bin` and `libgdal-dev` (already added). If you still see build errors, check the `pip` error log for missing headers and add corresponding `-dev` packages.
- Missing environment variables: `apis/ocean_news.py` raises when `GEMINI_API_KEY` is not present; set it in Railway variables before first run.
- Large image size: the image uses `python:3.11-slim` but installs GDAL; you can optimize later by using multi-stage builds or a smaller base image.

## Next steps / improvements

- Pin versions in `requirements.txt` for reproducible builds.
- Add a small health endpoint and readiness probe to help platform orchestrators.
- Add CI build to ensure the Docker image builds on push.

---

If you'd like, I can:
- Pin dependency versions and update `requirements.txt`.
- Add a small `health` endpoint.
- Add a tiny GitHub Actions workflow that builds the Docker image on push.
